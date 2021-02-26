from tkinter import StringVar, BooleanVar, filedialog
from ttkthemes.themed_tk import ThemedTk, ttk
import threading
import youtube_dl
import pickle
from urllib.request import urlopen
from io import BytesIO
from PIL import ImageTk, Image
import shutil
from os import path

class YdlLogger(object):
    def debug(self, msg):
        print("Logger debug:", msg)

    def warning(self, msg):
        print("Logger warning:", msg)
        consolePrint(msg)

    def error(self, msg):
        print("Logger error:", msg)
        consolePrint(msg)

def ydl_hook(response):
    if response['status'] == 'downloading':
        downloaded_percent = (response["downloaded_bytes"]*100)/response["total_bytes"]
        speed = response["speed"]
        eta = response["eta"]
        elapsed = response["elapsed"]

        pgb_download['value'] = downloaded_percent
        var_download_percentage.set(str(round(downloaded_percent)) + "%")
        var_download_speed.set("Download speed: " + str(round(speed / 1000000, 1)) + "Mbps")
        var_download_eta.set("Time remaining: " + str(eta) + "s")
        var_download_elapsed.set("Time elapsed: " + str(round(elapsed)) + "s")

    if response['status'] == 'finished':
        consolePrint('Done downloading, now converting ...')

def enteredLink(*args):
    threading.Thread(target=getVideoInfo).start()

def selectPlaylistDownload():
    if (var_download_playlist_range.get()):
        ent_playlist_from["state"] = "enable"
        ent_playlist_to["state"] = "enable"
    else:
        ent_playlist_from["state"] = "disabled"
        ent_playlist_to["state"] = "disabled"

def setDefaultDownloadLocation():
    folderPath = filedialog.askdirectory()
    var_default_download_folder.set(folderPath)
    var_download_folder.set(folderPath)
    pickle.dump({"download_location": folderPath}, open("save.p", "wb"))

def getDefaultDownloadLocation():
    folderPath = pickle.load(open("save.p", "rb"))["download_location"]
    var_default_download_folder.set(folderPath)
    var_download_folder.set(folderPath)

def selectDownloadFolder():
    folderPath = filedialog.askdirectory()
    var_download_folder.set(folderPath)

def downloadVideoButtonPressed():
    threading.Thread(target=downloadVideo).start()
    
def downloadVideo():
    if var_link.get() == "":
        consolePrint("Invalid link")
        return

    consolePrint("Downloading...")

    ydl_opts = {}

    ydl_opts["ignoreerrors"] = True
    ydl_opts["geo_bypass"] = True
    ydl_opts["cachedir"] = False
    ydl_opts["nocheckcertificate"] = True
    ydl_opts["progress_hooks"] = [ydl_hook]
    ydl_opts["logger"] = YdlLogger()

    if "playlist" in var_link.get():
        ydl_opts["noplaylist"] = False
        if var_download_playlist_range.get():
            ydl_opts["playliststart"] = int(var_from_video.get())
            ydl_opts["playlistend"] = int(var_to_video.get())
    else:
        ydl_opts["noplaylist"] = True

    ydl_opts["prefer_ffmpeg"] = True
    
    postprocessors = []
    if var_audio_only.get():
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        })
    if var_embed_metadata.get():
        postprocessors.append({
            'key': 'FFmpegMetadata',
        })
    if var_embed_thumbnail.get():
        ydl_opts["writethumbnail"] = True
        postprocessors.append({
            'key': 'EmbedThumbnail',
        })  
    if var_embed_subtitles.get():
        postprocessors.append({
            'key': 'FFmpegEmbedSubtitle',
        })    
    ydl_opts["postprocessors"] = postprocessors

    ydl_opts["format"] = "mp4"

    ydl_opts["outtmpl"] = var_download_folder.get() + "/" + "%(title)s.%(ext)s"

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([var_link.get()])

    consolePrint("Complete!")

def getVideoInfo():
    if var_link.get() == "":
        consolePrint("Invalid link")
        return

    if "playlist" in var_link.get():
        consolePrint("Cannot get info for playlists yet")
        return

    consolePrint("Gathering info...")

    ydl_opts = {}

    ydl_opts["ignoreerrors"] = True
    ydl_opts["geo_bypass"] = True
    ydl_opts["cachedir"] = False
    ydl_opts["nocheckcertificate"] = True
    ydl_opts["noplaylist"] = True
    ydl_opts["writethumbnail"] = True
    ydl_opts["skip_download"] = True
    ydl_opts["logger"] = YdlLogger()
    ydl_opts["outtmpl"] = "./temp/%(title)s.%(ext)s"

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        meta = ydl.extract_info(var_link.get())
        var_info_title.set("Title: " + meta["title"])
        var_info_uploader.set("Channel: " + meta["uploader"])
        var_info_views.set("Views: " + str(meta["view_count"]))
        var_info_likes.set("Likes: " + str(meta["like_count"]))
        var_info_dislikes.set("Dislikes: " + str(meta["dislike_count"]))
        var_info_upload_date.set("Upload date: " + meta["upload_date"])
        var_info_format.set("Format: " + meta["format"])
        var_info_duration.set("Duration: " + str(meta["duration"]) + "s")
        
        url = meta["thumbnails"][0]["url"]
        url_image = urlopen(url)
        data = url_image.read()
        url_image.close()
        im = Image.open(BytesIO(data))
        im = im.resize(imageScale(im, 160), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(im)
        lbl_thumbnail.configure(image=image)
        lbl_thumbnail.image = image

    consolePrint("")

def imageScale(img, new_height):
    old_size = img.size
    aspect_ratio = old_size[1] / old_size[0]
    new_width = new_height / aspect_ratio
    new_size = (round(new_width), round(new_height))
    return new_size

def consolePrint(msg):
    var_console_output.set("Console output: " + msg)

##################################### Window setup
window = ThemedTk(theme='breeze')
window.title("MP3 Downloader")
window.iconbitmap("icon.ico")

##################################### Create Tkinter variables
var_link = StringVar(window)
var_link.trace_add('write', enteredLink)

var_audio_only = BooleanVar(window)
var_embed_thumbnail = BooleanVar(window)
var_embed_metadata = BooleanVar(window)
var_embed_subtitles = BooleanVar(window)

var_download_playlist_range = BooleanVar(window)
var_from_video = StringVar(window)
var_to_video = StringVar(window)

var_download_percentage = StringVar(window, "0%")
var_download_speed = StringVar(window, "Download speed: ")
var_download_eta = StringVar(window, "Time remaining: ")
var_download_elapsed = StringVar(window, "Time elapsed: ")

var_info_title = StringVar(window, "Title: ")
var_info_uploader = StringVar(window, "Channel:")
var_info_views = StringVar(window, "Views:")
var_info_likes = StringVar(window, "Likes:")
var_info_dislikes = StringVar(window, "Dislikes:")
var_info_upload_date = StringVar(window, "Upload date:")
var_info_format = StringVar(window, "Format:")
var_info_duration = StringVar(window, "Duration:")

var_download_folder = StringVar(window)
var_default_download_folder = StringVar(window)

var_console_output = StringVar(window, "Console output: ")

##################################### Create widgets
nb_main = ttk.Notebook(window)

# Download video tab
frm_download = ttk.Frame(nb_main)

# Video link
frm_link = ttk.Frame(frm_download)
ent_link = ttk.Entry(frm_link, textvariable=var_link, width=155)

# Format options
frm_format_opts = ttk.Frame(frm_download)
lbl_format_opts = ttk.Label(frm_format_opts, text="Format options")
chk_audio_only = ttk.Checkbutton(frm_format_opts, text="Audio only", variable=var_audio_only)
chk_embed_thumbnail = ttk.Checkbutton(frm_format_opts, text="Thumbnail", variable=var_embed_thumbnail)
chk_embed_metadata = ttk.Checkbutton(frm_format_opts, text="Metadata", variable=var_embed_metadata)
chk_embed_subtitles = ttk.Checkbutton(frm_format_opts, text="Subtitles", variable=var_embed_subtitles)

sep_format_opts = ttk.Separator(frm_download, orient='horizontal')

# Playlist options
frm_playlist = ttk.Frame(frm_download)
lbl_playlist_opts = ttk.Label(frm_playlist, text="Playlist options")
chk_dwnl_playlist_range = ttk.Checkbutton(frm_playlist, text="Playlist range", command=selectPlaylistDownload, variable=var_download_playlist_range)
frm_playlist_range = ttk.Frame(frm_playlist)
lbl_playlist_from = ttk.Label(frm_playlist_range, text="From")
ent_playlist_from = ttk.Entry(frm_playlist_range, textvariable=var_from_video, width=8, state="disabled")
lbl_playlist_to = ttk.Label(frm_playlist_range, text="To")
ent_playlist_to = ttk.Entry(frm_playlist_range, textvariable=var_to_video, width=8, state="disabled")

sep_playlist_opts = ttk.Separator(frm_download, orient='horizontal')

# Download location options
frm_download_folder = ttk.Frame(frm_download)
lbl_download_folder = ttk.Label(frm_download_folder, text="Download location")
ent_download_folder = ttk.Entry(frm_download_folder, textvariable=var_download_folder, width=60)
btn_download_folder = ttk.Button(frm_download_folder, text="Open", command=selectDownloadFolder)

sep_download_folder = ttk.Separator(frm_download, orient='horizontal')

# Download video button
frm_download_info = ttk.Frame(frm_download)
btn_download = ttk.Button(frm_download_info, text="Download", command=downloadVideoButtonPressed)
pgb_download = ttk.Progressbar(frm_download_info, length=300, orient="horizontal", mode="determinate")
lbl_download_percentage = ttk.Label(frm_download_info, textvariable=var_download_percentage)
sep_download_info1 = ttk.Separator(frm_download_info, orient='vertical')
lbl_download_speed = ttk.Label(frm_download_info, textvariable=var_download_speed)
sep_download_info2 = ttk.Separator(frm_download_info, orient='vertical')
lbl_download_eta = ttk.Label(frm_download_info, textvariable=var_download_eta)
sep_download_info3 = ttk.Separator(frm_download_info, orient='vertical')
lbl_download_elapsed = ttk.Label(frm_download_info, textvariable=var_download_elapsed)

sep_download_buttons = ttk.Separator(frm_download, orient='horizontal')

lbl_console_output = ttk.Label(frm_download, textvariable=var_console_output)

sep_vertical = ttk.Separator(frm_download, orient='vertical')

# Info panel on the right
frm_video_info = ttk.Frame(frm_download)
im = Image.open("default_thumbnail.png")
im = im.resize(imageScale(im, 160), Image.ANTIALIAS)
default_thumbnail_image = ImageTk.PhotoImage(im)
lbl_thumbnail = ttk.Label(frm_video_info, image=default_thumbnail_image, width=10)
lbl_info_title = ttk.Label(frm_video_info, textvariable=var_info_title)
lbl_info_uploader = ttk.Label(frm_video_info, textvariable=var_info_uploader)
lbl_info_views = ttk.Label(frm_video_info, textvariable=var_info_views)
frm_likes_dislikes = ttk.Frame(frm_video_info)
lbl_info_likes = ttk.Label(frm_likes_dislikes, textvariable=var_info_likes)
lbl_info_dislikes = ttk.Label(frm_likes_dislikes, textvariable=var_info_dislikes)
lbl_info_upload_date = ttk.Label(frm_video_info, textvariable=var_info_upload_date)
lbl_info_format = ttk.Label(frm_video_info, textvariable=var_info_format)
lbl_info_duration = ttk.Label(frm_video_info, textvariable=var_info_duration)

# Settings tab
frm_settings = ttk.Frame(nb_main)

frm_settings_dl_loc = ttk.Frame(frm_settings)
lbl_settings_dl_loc = ttk.Label(frm_settings_dl_loc, text="Default download location:")
ent_settings_dl_loc = ttk.Entry(frm_settings_dl_loc, textvariable=var_default_download_folder, width=60)
btn_settings_dl_loc = ttk.Button(frm_settings_dl_loc, text="Open", command=setDefaultDownloadLocation)

lbl_settings_info = ttk.Label(frm_settings, text="Made by nikinaxx")

##################################### Place widgets in frames
# Place link in frame
frm_link.grid(row=0, column=0, columnspan=3, sticky='nswe', padx=5, pady=(10,5))
ent_link.grid(row=0, column=0, sticky='nswe')

# Place format options in frame
frm_format_opts.grid(row=1, column=0, sticky='w', padx=5, pady=5)
lbl_format_opts.grid(row=0, column=0, sticky='w', padx=5, pady=5)
chk_audio_only.grid(row=1, column=0, sticky='w', padx=5, pady=5)
chk_embed_thumbnail.grid(row=1, column=1, sticky='w', padx=5, pady=5)
chk_embed_metadata.grid(row=1, column=2, sticky='w', padx=5, pady=5)
chk_embed_subtitles.grid(row=1, column=3, sticky='w', padx=5, pady=5)

sep_format_opts.grid(row=2, column=0, sticky='we', padx=5, pady=5)

# Place playlist options in frame
frm_playlist.grid(row=3, column=0, sticky='w', padx=5, pady=5)
lbl_playlist_opts.grid(row=0, column=0, sticky='w', padx=5, pady=5)
chk_dwnl_playlist_range.grid(row=1, column=0, sticky='w', padx=5, pady=5)
frm_playlist_range.grid(row=2, column=0, sticky='w', padx=5)
lbl_playlist_from.grid(row=0, column=0, sticky='w', padx=5, pady=5)
ent_playlist_from.grid(row=0, column=1, sticky='w', padx=5, pady=5)
lbl_playlist_to.grid(row=0, column=2, sticky='w', padx=5, pady=5)
ent_playlist_to.grid(row=0, column=3, sticky='w', padx=5, pady=5)

sep_playlist_opts.grid(row=4, column=0, sticky='we', padx=5, pady=5)

# Place download location options in frame
frm_download_folder.grid(row=5, column=0, sticky='w', padx=5, pady=5)
lbl_download_folder.grid(row=0, column=0, sticky='w', padx=5, pady=5)
ent_download_folder.grid(row=1, column=0, sticky='w', padx=5, pady=5)
btn_download_folder.grid(row=1, column=1, sticky='w', padx=5, pady=5)

sep_download_folder.grid(row=6, column=0, columnspan=3, sticky='we', padx=5, pady=5)

# Place download button in frame
frm_download_info.grid(row=7, column=0, columnspan=3, sticky='we', padx=5, pady=5)
btn_download.grid(row=0, column=0, sticky='w', padx=5, pady=5)
pgb_download.grid(row=0, column=1, sticky='w', padx=5, pady=5)
lbl_download_percentage.grid(row=0, column=3, sticky='w', padx=5, pady=5)
sep_download_info1.grid(row=0, column=4, sticky='ns', padx=5, pady=5)
lbl_download_speed.grid(row=0, column=5, sticky='w', padx=5, pady=5)
sep_download_info2.grid(row=0, column=6, sticky='ns', padx=5, pady=5)
lbl_download_eta.grid(row=0, column=7, sticky='w', padx=5, pady=5)
sep_download_info3.grid(row=0, column=8, sticky='ns', padx=5, pady=5)
lbl_download_elapsed.grid(row=0, column=9, sticky='w', padx=5, pady=5)

sep_download_buttons.grid(row=8, column=0, columnspan=3, sticky='we', padx=5, pady=5)

lbl_console_output.grid(row=9, column=0, columnspan=3, sticky='w', padx=10, pady=(5,10))

sep_vertical.grid(row=1, rowspan=5, column=1, sticky='nsw', padx=5, pady=5)

# Place info panel in frame
frm_video_info.grid(row=1, rowspan=5, column=2, sticky='nswe', padx=5, pady=5)
lbl_thumbnail.grid(row=0, rowspan=4, column=0, sticky='w', padx=5, pady=5)
lbl_info_uploader.grid(row=0, column=1, sticky='w', padx=5, pady=5)
lbl_info_views.grid(row=1, column=1, sticky='w', padx=5, pady=5)
frm_likes_dislikes.grid(row=2, column=1, sticky='w', pady=5)
lbl_info_likes.grid(row=0, column=0, sticky='w', padx=5)
lbl_info_dislikes.grid(row=0, column=1, sticky='w', padx=5)
lbl_info_upload_date.grid(row=3, column=1, sticky='w', padx=5, pady=5)
lbl_info_title.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=5)
lbl_info_format.grid(row=5, column=0, columnspan=2, sticky='w', padx=5, pady=5)
lbl_info_duration.grid(row=6, column=0, columnspan=2, sticky='w', padx=5, pady=5)

# Place settings in frame
frm_settings_dl_loc.grid(row=0, column=0, sticky='nswe', padx=5, pady=(10,5))
lbl_settings_dl_loc.grid(row=0, column=0, sticky='w', padx=5, pady=5)
ent_settings_dl_loc.grid(row=0, column=1, sticky='w', padx=5, pady=5)
btn_settings_dl_loc.grid(row=0, column=2, sticky='w', padx=5, pady=5)

lbl_settings_info.grid(row=1, column=0, sticky='w', padx=10, pady=5)

##################################### Configure stretching
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)
frm_download.columnconfigure(2, weight=1)
frm_download.rowconfigure(0, weight=1)

##################################### Place frames in tab
nb_main.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
frm_download.grid(row=0, column=0, sticky='nsew')
frm_settings.grid(row=0, column=0, sticky='nsew')

##################################### Create Tkinter tabs
nb_main.add(frm_download, text="Download")
nb_main.add(frm_settings, text="Settings")

##################################### Mainloop
getDefaultDownloadLocation()
window.mainloop()

##################################### On exit
if path.exists("./temp"):
    shutil.rmtree("./temp")