"""
Replaces builtin FFmpegSplitChaptersPP by adding ability to also set metadata for split files.
For now only artist field supported
Do not use --split-chapters flag when this postprocesser enabled.
"""
from yt_dlp.postprocessor import FFmpegPostProcessor
from yt_dlp.postprocessor.common import PostProcessor
from yt_dlp.utils import encodeFilename
import re
import sys


# Adds convenient --regex option to yt-dlp to specify title split regex
#
# It's done in hacky way to directly modifying sys.argv before yt-dlp runs
# because yt-dlp does not allow to add postprocesstors on runtime.
# While SplitAndTag runs either before or after video downloaded depending on
# --skip-download specified
def hijack_args():
    args_map = {}
    regex_index = -1
    has_skip_video = False
    arg_template = "SplitAndTag:when={};regex={}"

    for i, arg in enumerate(sys.argv):
        args_map[i] = arg
        if arg == "--regex":
            regex_index = i
        if arg == "--skip-download":
            has_skip_video = True
    new_args = []
    skip_next_arg = False
    if regex_index > 0:
        for key, value in sorted(args_map.items()):
            if skip_next_arg:
                skip_next_arg = False
                continue
            if key == regex_index:
                new_args.append("--use-postprocessor")
                when = 'before_dl' if has_skip_video else 'after_move'
                new_args.append(
                    arg_template.format(when, args_map[regex_index + 1]))
                skip_next_arg = True
            else:
                new_args.append(value)
        sys.argv.clear()
        sys.argv.extend(new_args)
    return f"{' '.join(sys.argv[1:])}"


new_args = hijack_args()
print("Modified yt-dlp args: {}".format(new_args))


class SplitAndTagPP(FFmpegPostProcessor):
    def __init__(self, downloader, force_keyframes=False, regex=''):
        FFmpegPostProcessor.__init__(self, downloader)
        self._force_keyframes = force_keyframes
        self.regex = regex
        self.skip_download = True

    def _prepare_filename(self, number, chapter, info):
        info = info.copy()
        info.update({
            'section_number': number,
            'section_title': chapter.get('title'),
            'section_start': chapter.get('start_time'),
            'section_end': chapter.get('end_time'),
        })
        return self._downloader.prepare_filename(info, 'chapter')

    def _ffmpeg_args_for_chapter(self, number, chapter, info):
        destination = self._prepare_filename(number, chapter, info)
        if not self._downloader._ensure_dir_exists(encodeFilename(destination)):
            return

        chapter['filepath'] = destination
        return (
            destination,
            ['-ss', str(chapter['start_time']),
             '-t', str(chapter['end_time'] - chapter['start_time'])
             ])

    # FFmpeg adds metadata about all chapters from parent file to all split m4a files.
    # This is incorrect since there must be only single chapter in each file after split.
    # Such behavior confuses players who think multiple chapters present
    def _set_out_opts(self, ext, chapter_title):
        out_opts = [*self.stream_copy_opts()]
        out_opts.extend(['-map_metadata', '0'])
        # exclude chapters metadata but keep everything else
        out_opts.extend(['-map_chapters', '-1'])
        if len(self.regex) > 0:
            # use regex to map multiple fields from the chapter title
            out_opts.extend(self._get_metadata_from_title(ext, chapter_title))
        else:
            # replace global title with chapter title
            out_opts.extend(self._map_title_from_chapter(ext, chapter_title))
        return out_opts

    # Generates correct metadata arg depending on file format
    # tested on youtube opus and m4a music videos with chapters
    # TODO check for other formats with chapters: MP3, flac , aac, ogg
    def _metadata_flag(self, ext):
        return '-metadata:s' if ext == 'opus' else '-metadata'

    def _map_title_from_chapter(self, ext, chapter_title):
        out_opts = []
        if not chapter_title:
            return out_opts
        # was tested only on youtube music videos with m4a and opus
        if ext not in ['m4a', 'opus']:
            return out_opts
        # replace global title with chapter specific title in split files
        if self.skip_download:
            self.to_screen("Set title={}".format(chapter_title))
        return [self._metadata_flag(ext), 'title={}'.format(chapter_title)]

    def _get_metadata_from_title(self, ext, chapter_title):
        opts = []
        if not chapter_title:
            return opts
        keywords = {"%artist": -1, "%album": -1, "%track": -1, "%title": -1}
        new_regex = self.regex
        for key in keywords.keys():
            index = self.regex.find(key)
            if index > -1:
                keywords[key] = index
                new_regex = new_regex.replace(key, "(.+)")
        sorted_by_index = sorted(keywords.items(), key=lambda item: item[1])
        sorted_keywords = [item[0] for item in sorted_by_index if item[1] >= 0]
        match = re.match(new_regex, chapter_title)
        if not match:
            self.to_screen(
                "No data matching regex {} found".format(self.regex))
            return opts
        # Could happen if title contains keywords
        # Do not account for such case as of now
        if len(sorted_keywords) != len(match.groups()):
            self.to_screen(
                "Regex {} has {} arguments. But {} found: {}".format(
                    new_regex, len(match.groups()),
                    len(sorted_keywords), sorted_keywords))
            exit()
        log_string = ""
        for i, group in enumerate(match.groups()):
            value = group.strip()
            tag_name = sorted_keywords[i]
            log_string = "{} {}='{}'".format(log_string, tag_name[1:], value)
            opts.extend([
                self._metadata_flag(ext),
                # eg. artist=some_artist
                "{}={}".format(tag_name[1:], value)])
        self.to_screen("Set{}".format(log_string), quiet=False)
        return opts

    @PostProcessor._restrict_to(images=False)
    def run(self, info):
        # filename absent when --skip-download passed
        self.skip_download = False if 'filepath' in info else True
        self._fixup_chapters(info)
        chapters = info.get('chapters') or []
        if not chapters:
            self.to_screen('Chapter information is unavailable')
            return [], info
        if self.skip_download:
            for idx, chapter in enumerate(chapters):
                title = chapter.get('title', '')
                self._get_metadata_from_title(info['ext'], title)
            return [], info

        in_file = info['filepath']
        if self._force_keyframes and len(chapters) > 1:
            in_file = self.force_keyframes(
                in_file,
                (c['start_time'] for c in chapters))

        self.to_screen(
            'Splitting video by chapters; %d chapters found' % len(chapters))
        for idx, chapter in enumerate(chapters):
            title = chapter.get('title', '')
            out_file_opts = self._set_out_opts(info['ext'], title)
            destination, opts = self._ffmpeg_args_for_chapter(
                idx + 1, chapter, info)
            if not self.skip_download:
                self.real_run_ffmpeg(
                    [(in_file, opts)],
                    [(destination, out_file_opts)])
        # os.remove(in_file)
        return [], info
