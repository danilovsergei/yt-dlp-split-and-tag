A [yt-dlp](https://github.com/yt-dlp/yt-dlp) postprocessor [plugin](https://github.com/yt-dlp/yt-dlp#plugins) for splitting youtube videos 
by chapter and set metadata.
It designed to be used instead of yt-dlp built in FFmpegSplitChaptersPP post processor because of the bug in ffmpeg.
There is a bug in ffmpeg splitting m4a files by chapter. Ffmpeg writes full chapters list in each split file.
And it confuses players.

SplitAndTag instead writes only information about the track to split files.


## Installation

Requires yt-dlp `2023.01.01` or above.

You can install this package with pip:

```
python3 -m pip install -U https://github.com/danilovsergei/yt-dlp-split-and-tag/releases/download/master/yt-dlp-split-and-tag.zip
```

Or either copy to the relevant directory manually by following [yt-dlp installing plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins)

## Usage

Pass `--use-postprocessor SplitAndTag:when=after_move` to activate the PostProcessor. 
Do not use --split-chapters together with SplitAndTag to avoid conflicts with builtin FFmpegSplitChaptersPP
SplitAndTag will automatically start splitting once enabled
