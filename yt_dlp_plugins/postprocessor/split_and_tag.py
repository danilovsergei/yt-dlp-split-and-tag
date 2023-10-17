"""
Replaces builtin FFmpegSplitChaptersPP by adding ability to also set metadata for split files.
For now only artist field supported
Do not use --split-chapters flag when this postprocesser enabled.
"""
from yt_dlp.postprocessor import FFmpegPostProcessor
from yt_dlp.postprocessor.common import PostProcessor
from yt_dlp.utils import (
    encodeFilename,
)
import os

class SplitAndTagPP(FFmpegPostProcessor):
    def __init__(self, downloader, force_keyframes=False, tag_regex=''):
        FFmpegPostProcessor.__init__(self, downloader)
        self._force_keyframes = force_keyframes
        self.tag_regex = tag_regex

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
        self.to_screen('Chapter %03d; Destination: %s' % (number, destination))
        return (
            destination,
            ['-ss', str(chapter['start_time']),
             '-t', str(chapter['end_time'] - chapter['start_time'])
             ])
    
    def _set_out_opts(self, ext, chapter_title):
        if ext == 'm4a':
            return [
                *self.stream_copy_opts(),
                # For m4a ffmpeg copies all available parent track chapters to split tracks metadata
                # And such behavior confuses players
                # Wipe parent track metadata from split tracks and fill out only title
                '-metadata', 'title={}'.format(chapter_title),
                '-map_metadata','-1']
        else:
            return self.stream_copy_opts()

    @PostProcessor._restrict_to(images=False)
    def run(self, info):
        self._fixup_chapters(info)
        chapters = info.get('chapters') or []
        if not chapters:
            self.to_screen('Chapter information is unavailable')
            return [], info

        in_file = info['filepath']
        if self._force_keyframes and len(chapters) > 1:
            in_file = self.force_keyframes(in_file, (c['start_time'] for c in chapters))
        self.to_screen('Splitting video by chapters; %d chapters found' % len(chapters))
        
        for idx, chapter in enumerate(chapters):
            out_file_opts = self._set_out_opts(info['ext'], chapter['title'])
            destination, opts = self._ffmpeg_args_for_chapter(idx + 1, chapter, info)
            self.real_run_ffmpeg([(in_file, opts)], [(destination, out_file_opts)])
        os.remove(in_file)
        return [], info

