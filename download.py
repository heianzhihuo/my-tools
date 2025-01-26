import argparse
from concurrent.futures import ThreadPoolExecutor
import getpass
import hashlib
import json
import os.path
import sys
import time
import traceback
from typing import Dict, List
from urllib.parse import quote

import requests

def print_split():
    print("\n\n--------------------------\n")


def parallel_download(url: str, local_dir: str, file_name: str, file_size: int = None, proxies: dict = None) -> bool:
    PART_SIZE = 160 * 1024 * 1024  # every part is 160M
    file_path = os.path.join(local_dir, file_name)
    tasks = [(file_path, idx*PART_SIZE, (idx+1)*PART_SIZE, url, proxies)
             for idx in range(int(file_size / PART_SIZE))]
    if file_size % PART_SIZE != 0:
        tasks.append((file_path, int(file_size / PART_SIZE)*PART_SIZE, file_size, url, proxies))
    parallels = 4
    print(f"starting to download {file_name} with {len(tasks)} parts")
    with ThreadPoolExecutor(max_workers=parallels, thread_name_prefix="download") as executor:
        part_file_names = list(executor.map(part_download, tasks))
    print(f"finished download {file_name} with {len(tasks)} parts")
    with open(file_path, 'rb') as f:
        for part_file_name in part_file_names:
            with open(part_file_name, 'rb') as part_file:
                f.write(part_file.read())
            os.remove(part_file_name)
    return True


def part_download(params) -> str:
    file_path, start, end, url, proxies = params
    headers = {'Range': f'bytes={start}-{end}'}
    part_file_name = file_path + f"_{start}_{end}"
    try:
        r = requests.get(url, headers=headers, stream=True, proxies=proxies)
        r.raise_for_status()
        with open(part_file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=4*1024*1024):
                f.write(chunk)
        return part_file_name
    except Exception as e:
        print(f"part_download failed with {e}")
        return None


def download_from_url(base_dir: str, url: str, proxies: dict = None, chunk_size: int = 50*1024*1024) -> str:
    """从url下载文件到base_dir目录"""
    try:
        response = requests.get(url, stream=True, proxies=proxies, verify=False)
        response.raise_for_status()
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


class HuggingFace:

    """
    Hugging Face 无sha校验
    """

    endpoint = "https://huggingface.co"

    @classmethod
    def get_files(cls, repo_id: str, revision: str = "main", proxies: Dict = None) -> List[str]:
        url = (
            f"{cls.endpoint}/api/models/{repo_id}"
            if revision is None
            else f"{cls.endpoint}/api/models/{repo_id}/revision/{quote(revision,safe='')}"
        )
        try:
            response = requests.get(url, proxies=proxies, verify=False)
            response.raise_for_status()
            resp_json = response.json()
            return [file["rfilename"] for file in resp_json["siblings"]]
        except Exception as e:
            print(f"获取文件列表失败：url = {url} {e}")
            traceback.print_exc()
            return []

    @classmethod
    def download_model(cls, repo_id: str, base_dir: str, proxies: dict = None, revision: str = "main"):
        base_dir = os.path.join(base_dir, repo_id)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        print(f"begin download model {repo_id} revision {revision} from Hugging Face!")
        files = cls.get_files(repo_id, revision, proxies)
        time_start = time.time()
        success_cnt = 0
        for file in files:
            print_split()
            url = f"{cls.endpoint}/{repo_id}/resolve/{quote(revision,safe='')}/{quote(file)}"
            if download_from_url(base_dir, url, proxies=proxies) is not None:
                success_cnt += 1
            else:
                print(f"download file {file} in {repo_id} from Hugging Face failed. base_dir = {base_dir}")
        m, s = divmod(time.time() - time_start, 60)
        h, m = divmod(m, 60)
        print(
            f"{success_cnt}/{len(files)} file download completed, cost time: {int(h):0>d}h {int(m):0>2d}m {int(s):0>2d}s"
        )
        print(f"success download model {repo_id} revision {revision} from Hugging Face!")


class ModelScope:

    """
    Model Scope 校验sha避免重复下载
    """
    base_url = "https://modelscope.cn/api/v1/models"

    @classmethod
    def get_revisions(cls, model_name: str, proxies: dict = None) -> List[str]:
        url = f"{cls.base_url}/{model_name}/revisions"
        try:
            response = requests.get(url, proxies=proxies, verify=False)
            response.raise_for_status()
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
            response.raise_for_status()
            resp_json = response.json()
            return [{"path": _["Path"], "sha256": _["Sha256"]} for _ in resp_json["Data"]["Files"]]
        except Exception as e:
            print(f"获取文件列表失败：url = {url} {e}")
            traceback.print_exc()
            return []

    @classmethod
    def download_model(cls, repo_id: str, base_dir: str, proxies: dict = None, chunk_size: int = 50 * 1024 * 1024):
        base_dir = os.path.join(base_dir, repo_id)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        print(f"begin download model {repo_id} from model scope!")
        revisions = cls.get_revisions(repo_id, proxies)
        if len(revisions) == 0:
            print(f"没有找到版本列表：model_name = {repo_id}")
            return
        revision = revisions[0]
        print(f"使用版本：{revision}")
        files = cls.get_files(repo_id, revision, proxies)
        if len(files) == 0:
            print(f"没有文件列表：model_name = {repo_id}, revision = {revision}")
            return
        time_start = time.time()
        success_cnt = 0
        for file in files:
            print_split()
            file_path, hash = file["path"], file["sha256"]
            local_file_path = os.path.join(base_dir, file_path)
            if os.path.exists(local_file_path) and file_hash(local_file_path) == hash:
                success_cnt += 1
                continue
            url = f"{cls.base_url}/{repo_id}/repo?Revision={revision}&FilePath={file_path}"
            if download_from_url(base_dir, url, proxies, chunk_size) is not None:
                success_cnt += 1
        m, s = divmod(time.time() - time_start, 60)
        h, m = divmod(m, 60)
        print(
            f"{success_cnt}/{len(files)} file download completed, cost time: {int(h):0>d}h {int(m):0>2d}m {int(s):0>2d}s"
        )
        print(f"success download model {repo_id} from model scope!")
