A [yt-dlp](https://github.com/yt-dlp/yt-dlp) postprocessor [plugin](https://github.com/yt-dlp/yt-dlp#plugins) for splitting videos by chapter and set metadata based on chapter title.\
It designed as more feature rich replacement for yt-dlp --split-chapters option

## Features
* Strips chapters information from split files. Default --split-chapters adds all chapters metadata to each split file. See [bug/8363](https://github.com/yt-dlp/yt-dlp/issues/8363). Audio playes load split files incorrectly 
* Allows to extract artist , title , album from chapter title using regex. Default --split-chapters writes the same title/artist to each split file
* Provides conveninent --regex parameter to yt-dlp to perform chapter title parsing

## Installation

Requires yt-dlp `2023.01.01` or above.

You can install this package with pip:

```
python3 -m pip install -U https://github.com/danilovsergei/yt-dlp-split-and-tag/releases/download/master/yt-dlp-split-and-tag.zip
```

Or either copy to the relevant directory manually by following [yt-dlp installing plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins)

Tested way on Linux is to unpack [release](https://github.com/danilovsergei/yt-dlp-split-and-tag/releases/download/master/yt-dlp-split-and-tag.zip) to /home/$USER/.yt-dlp/plugins/SplitAndTag/

## Usage examples
### Only print information how chapter title will be split
Use these options to quickly find out correct regex for the chapter title format.\
It only prints what artist/title/album tags will be written after split.\
No video is downloaded. No files are being tagged.\
Whole command takes couple of seconds

Url in example below has title for each chapter formatted as '1. Artist - Title'
```
yt-dlp --extract-audio --skip-download --regex '%track\.%artist-%title' https://www.youtube.com/watch?v=eunsZB9c0eA
```
* --regex '%track\.%artist-%title' tells to extract track number , artist and title accordinly
* --skip-download instructs yt-dlp to only print how split data will look like without downloading a full video.
eg.
```
[SplitAndTag] Set track='1' artist='Paipy & Sarah Russell' title='What Do I Do'
[SplitAndTag] Set track='2' artist='Sam Laxton, Altartica & Sarah Russell' title='To Find Me'
```

### Download file , split by chapters and tag all split files
Just remove --skip-download option to instruct yt-dlp to download the video and tag all split files.\
Use this option when regex is tested.

```
yt-dlp --extract-audio --regex '%track\.%artist-%title' https://www.youtube.com/watch?v=eunsZB9c0eA
```
