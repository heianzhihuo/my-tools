import argparse
import getpass
import hashlib
import json
import os.path
import sys
import time
import traceback
from typing import List

import requests

def download_from_url(base_dir: str, url: str, proxies: dict = None, chunk_size: int = 50*1024*1024) -> str:
    """从url下载文件到base_dir目录"""
    try:
        response = requests.get(url, stream=True, proxies=proxies, verify=False)
        if response.status_code != 200:
            print(f"下载文件失败：url = {url}")
            return None
    except Exception as e:
        print(f"下载文件失败：url = {url} f{e}")
        traceback.print_exc()
        return None
    disposition_split = response.headers.get("Content-Disposition", "").split("=")
    if len(disposition_split) <= 1:
        print(f"获取文件名失败：Disposition = {disposition_split}, url = {url}")
        return None
    if disposition_split[0] == "attachment;filename":
        filename = disposition_split[1]
    else:
        print(f"获取文件名失败：Disposition = {disposition_split}, url = {url}")
        return None
    file_size = int(response.headers["Content-Length"])
    h_size = file_size / 1024 / 1024 / 1024
    chunk_num = (file_size - 1) // chunk_size + 1
    cur_chunk = 0
    file_path = os.path.join(base_dir, filename)
    try:
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)
                cur_chunk += 1
                print("Downloading <{}> size: {:.2f}GB: {}/{} - {:.2f}%: "
                      .format(filename, h_size, cur_chunk, chunk_num, cur_chunk / chunk_num * 100),
                      "▋" * (int(cur_chunk / chunk_num * 50)))
                sys.stdout.flush()
        print("Downloading <{}> file success. file size: {:.2f}GB.".format(file_path, h_size))
        return file_path
    except Exception as e:
        print(f"保存文件失败：filename = {filename}, url = {url} {e}")
        traceback.print_exc()
        return None


def batch_download(base_dir: str, urls: List[str], proxies: dict = None, chunk_size: int = 50*1024*1024):
    print(f'begin downloading {len(urls)} files ...')
    settings["proxy_location"] = "cn2"
    if proxies is None:
        proxies = get_proxies()
    time_start = time.time()
    for url in urls:
        print_split()
        download_from_url(base_dir, url, proxies, chunk_size)
    time_end = time.time()
    seconds = time_end - time_start
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print("file download completed, cost time : {:0>d} h {:0>2d} m {:0>2d} s".format(int(h), int(m), int(s)))


def file_hash(file_path: str, method="sha256") -> str:
    if not os.path.isfile(file_path):
        print("file not exist: {}".format(file_path))
        return None
    hash_method = {"sha256": hashlib.sha256, "sha512": hashlib.sha512, "md5": hashlib.md5, "sha1": hashlib.sha1}[method]
    with open(file_path, "rb") as f:
        hash = hash_method()
        while chunk := f.read(1024*1024):
            hash.update(chunk)
        return hash.hexdigest()


class ModelScope:

    base_url = "https://modelscope.cn/api/v1/models"

    @classmethod
    def get_revisions(cls, model_name: str, proxies: dict = None) -> List[str]:
        url = f"{cls.base_url}/{model_name}/revisions"
        try:
            response = requests.get(url, proxies=proxies, verify=False)
            if response.status_code != 200:
                print(f"获取版本列表失败：url = {url}")
                return []
            resp_json = response.json()
            return [revision["Revision"] for revision in resp_json["Data"]["RevisionMap"]["Branches"]]
        except Exception as e:
            print(f"获取版本列表失败：url = {url} {e}")
            traceback.print_exc()
            return []

    @classmethod
    def get_files(cls, model_name: str, revision: str, proxies: dict = None) -> List[str]:
        url = f"{cls.base_url}/{model_name}/repo/files?Revision={revision}&Root="
        try:
            response = requests.get(url, proxies=proxies, verify=False)
            if response.status_code != 200:
               print(f"获取文件列表失败：url = {url}")
               return []
            resp_json = response.json()
            return [{"path": _["Path"], "sha256": _["Sha256"]} for _ in resp_json["Data"]["Files"]]
        except Exception as e:
            print(f"获取文件列表失败：url = {url} {e}")
            traceback.print_exc()
            return []

    @classmethod
    def download_model(cls, path: str, model_name: str, base_dir: str, proxies: dict = None, chunk_size: int = 50*1024*1024):
        base_dir = os.path.join(base_dir, path, model_name)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        model_name = f"{path}/{model_name}"
        print(f"begin download model {model_name} from model scope!")
        revisions = cls.get_revisions(model_name, proxies)
        if len(revisions) == 0:
            print(f"没有版本列表：model_name = {model_name}")
            return
        revision = revisions[0]
        print(f"使用版本：{revision}")
        files = cls.get_files(model_name, revision, proxies)
        if len(files) == 0:
            print(f"没有文件列表：model_name = {model_name}, revision = {revision}")
            return
        time_start = time.time()
        cnt = 0
        for file in files:
            print_split()
            file_path, hash = file["path"], file["sha256"]
            local_file_path = os.path.join(base_dir, file_path)
            if os.path.exists(local_file_path) and file_hash(local_file_path) == hash:
                cnt += 1
                continue
            url = f"{cls.base_url}/{model_name}/repo?Revision={revision}&FilePath={file_path}"
            if download_from_url(base_dir, url, proxies, chunk_size) is not None:
                cnt += 1
        time_end = time.time()
        seconds = time_end - time_start
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        print("{:d} file download completed, cost time : {:0>d} h {:0>2d} m {:0>2d} s".format(cnt, int(h), int(m), int(s)))
        print(f"success download model {model_name} from model scope!")


def backend_factory():
    session = requests.Session()
    session.verify = False
    session.trust_env = False
    return session
