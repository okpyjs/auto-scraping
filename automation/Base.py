import json
import os
import re
import shutil
import time
from pathlib import Path

import pymiere
import requests
from PIL import Image
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
# Try to load saved client credentials
gauth.LoadCredentialsFile("credentials")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("credentials")
drive = GoogleDrive(gauth)


class Base:
    def __init__(self) -> None:
        self.name = None
        self.path = None
        self.url = None
        self.driver_id = None
        self.article_path = None
        self.date_time = None
        self.article_head = None
        self.img_link = None
        self.comment_body_list = None
        self.result_movie_path = None

    def check_gif(self, local_path):
        gif = Image.open(local_path)
        try:
            gif.seek(1)
        except:  # noqa
            isanimated = False
        else:
            isanimated = True

        return isanimated

    def gif_to_jpg(local_path):
        try:
            im = Image.open(local_path)
        except OSError:
            print("Cant load", local_path)
        i = 0
        mypalette = im.getpalette()

        try:
            while 1:
                im.putpalette(mypalette)
                new_im = Image.new("RGB", im.size)
                new_im.paste(im)
                new_im.save(local_path)

                i += 1
                im.seek(im.tell() + 1)

        except:  # noqa
            pass

        return

    def download_upload_img(self, path: str, driver_id: str, link: str, name: str):
        try:
            # download image
            r = requests.get(link, stream=True)
            r.raw.decode_content = True
            # save image
            with open(f"{path}/{name}", "wb") as f:
                shutil.copyfileobj(r.raw, f)
        except:  # noqa
            return

        # if gif, change to jpg because premiere dosen't support animated image
        gif_flag = self.check_gif(f"{path}/{name}")
        if gif_flag:
            self.gif_to_jpg(f"{path}/{name}")

        # upload to google drive
        self.upload_file(driver_id, f"{path}/{name}")

    def save_upload_audio(self, local_path: str, driver_id: str, text: str):
        # servide url convert txt to speech
        api_url = "https://www.yukumo.net/api/v2/aqtk1/koe.mp3"
        # cut text
        if len(text) > 140:
            text = text[:140]
        params = {
            "type": "f1",
            "effect": "none",
            "boyomi": "true",
            "speed": "150",
            "volume": "100",
            "kanji": text,
        }
        # headers = {
        #     "user-agent": """user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
        #     (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"""
        # }

        # download and upload audio
        resp = requests.get(url=api_url, params=params)
        with open(local_path, "wb") as f:
            f.write(resp.content)
        self.upload_file(driver_id, local_path)
        return

    def save_upload_txt(self, local_path: str, driver_id: str, txt: str):
        with open(local_path, mode="w", encoding="utf-8") as f:
            f.write(txt)
        self.upload_file(driver_id, local_path)
        return

    def create_driver_directory(self, directory_name: str, parent_id="root"):
        file_metadata = {
            "title": directory_name,
            # "parents": [{"id": parent_id}],
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id != "root":
            file_metadata["parents"] = [{"id": parent_id}]
        folder = drive.CreateFile(file_metadata)
        folder.Upload()
        return folder["id"]

    def upload_file(self, driver_id: str, local_path: str):
        file_name = local_path.split("/")[-1]
        file_name = file_name.split("\\")[-1]
        file = drive.CreateFile({"title": file_name, "parents": [{"id": driver_id}]})
        file.SetContentFile(local_path)
        file.Upload()
        return file["id"]

    def run():
        pass

    def save_upload(self):
        print("downloading and uploading data set")
        # create local path
        Path(f"{self.article_path}/音声ファイル").mkdir(parents=True, exist_ok=True)
        Path(f"{self.article_path}/記事").mkdir(parents=True, exist_ok=True)
        Path(f"{self.article_path}/画像").mkdir(parents=True, exist_ok=True)

        # create driver path
        self.article_driver_id = self.create_driver_directory(
            f"{self.date_time}_{self.article_head}", self.driver_id
        )
        self.audio_driver_id = self.create_driver_directory(
            "音声ファイル", self.article_driver_id
        )
        self.comment_driver_id = self.create_driver_directory(
            "記事", self.article_driver_id
        )
        self.image_driver_id = self.create_driver_directory(
            "画像", self.article_driver_id
        )

        # save image
        [
            self.download_upload_img(
                f"{self.article_path}/画像",
                self.image_driver_id,
                x,
                f"{idx + 1}_img.jpg",
            )
            for idx, x in enumerate(self.img_link)
        ]

        # download audio and comment
        name_idx = 0
        for item in self.comment_body_list:
            try:
                if not re.findall(r"\w+", item):
                    continue

                name_idx += 1
                # temp_arr = re.findall(r"\w+", item)
                # file_name = str(idx) + "_" + temp_arr[1] + temp_arr[-1]
                file_name = item
                if len(item) > 5:
                    file_name = item[:5]

                if name_idx < 10:
                    file_name = f"0{name_idx}_{file_name}"
                else:
                    file_name = f"{name_idx}_{file_name}"

                self.save_upload_audio(
                    f"{self.article_path}/音声ファイル/{file_name}.mp3",
                    self.audio_driver_id,
                    item,
                )

                self.save_upload_txt(
                    f"{self.article_path}/記事/{file_name}.txt",
                    self.comment_driver_id,
                    item,
                )
            except:  # noqa
                name_idx -= 1
                continue
        with open(
            f"{self.article_path}/all_info.json", mode="w", encoding="utf-8"
        ) as f:
            json.dump(self.result, f, ensure_ascii=False)
        self.upload_file(self.article_driver_id, f"{self.article_path}/all_info.json")

    def run_premiere(self):
        print("running premiere")
        # copy default.prproj
        shutil.copyfile(
            "default.prproj", os.path.abspath(f"{self.article_path}/result.prproj")
        )
        os.popen(os.path.abspath(f"{self.article_path}/result.prproj"))

        for x in range(20):
            try:
                assert pymiere.objects.app.isDocumentOpen(), "loading"
                break
            except:  # noqa
                time.sleep(1)
                if x == 19:
                    assert False, "error running premiere"
        print("opened Premiere")
        # import files
        files_path = [
            os.path.abspath(f"{self.article_path}/音声ファイル/{x}")
            for x in os.listdir(f"{self.article_path}/音声ファイル")
        ]
        files_path += [
            os.path.abspath(f"{self.article_path}/画像/{x}")
            for x in os.listdir(f"{self.article_path}/画像")
        ]
        print("importing files")
        for file in files_path:
            try:
                pymiere.objects.app.project.importFiles(
                    [file],
                    True,
                    pymiere.objects.app.project.rootItem,
                    True,
                )
            except:  # noqa
                continue
        # print("saving premiere project")
        # pymiere.objects.app.project.saveAs(f"{self.article_path}/result.prproj")
        print("imported files")
        print("plz edit movie")
        while True:
            try:
                if pymiere.objects.app.isDocumentOpen():
                    time.sleep(3)
                else:
                    return
            except:  # noqa
                self.result_movie_path = os.path.abspath(
                    f"{self.article_path}/result.mp4"
                )
                if os.path.isfile(self.result_movie_path):
                    self.upload_file(self.article_driver_id, self.result_movie_path)
                print("completed\n")
                return
        # try:
        #     pymiere.objects.app.quit()
        # except Exception as e:
        #     print(e)