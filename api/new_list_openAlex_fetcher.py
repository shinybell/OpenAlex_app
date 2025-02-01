# import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
# import math
# import asyncio
# import aiohttp
# import time
# from dotenv import load_dotenv
# from utils.common_method import extract_id_from_url

# class OpenAlexPagenationDataFetcherAio:
#     """
#     aiohttpを使ってOpenAlexのAPIを非同期で呼び出すクラス。
#     元のOpenAlexPagenationDataFetcherと同じロジックを踏襲。
#     """
#     def __init__(self, endpoint_url, params, id, max_works, only_japanese=False, use_API_key=False):
#         load_dotenv()
#         self.output_log = True
#         self.max_workers = max_works
#         self.endpoint_url = endpoint_url
#         self.params = params
#         self.only_japanese = only_japanese
        
#         # author IDを整形
#         id = extract_id_from_url(id)
#         self.id = id.upper()
        
#         # APIキーの設定
#         if use_API_key:
#             self.api_key = os.getenv('API_KEY')
#             if not self.api_key:
#                 raise ValueError("API_KEYが環境変数に設定されていません。")
#             self.params["api_key"] = self.api_key
#             self.params["mailto"] = "t.ichikawa.bnv@gmail.com"
#             print("APIキーを使っています。")
#         else:
#             print("APIキーを使っていません。")

#         # この後にfetch_all()でセットする
#         self.meta = {}
#         self.all_results = []

#     async def fetch_all(self):
#         """
#         エントリポイント: meta情報の取得 + ページネーションデータ取得
#         元の__init__内でやっていた処理を「非同期関数」として分割
#         """
#         # 1. 最初に1回だけmeta情報を取得
#         meta, first_results = await self._meta_data_getter()
#         self.meta = meta
#         self.all_results = first_results

#         # 2. ページネーション処理
#         if self.meta and self.params.get("per_page"):
#             # 1回で取得が終わらない場合
#             if self.meta.get("count", 0) > self.params["per_page"]:
#                 if self.meta.get("count") <= 10000:
#                     # オフセットページネーション
#                     more = await self._fetch_all_data_with_offset_pagination()
#                     self.all_results.extend(more)
#                 else:
#                     # カーソルページネーション
#                     more = await self._fetch_all_data_with_cursor_pagination()
#                     self.all_results.extend(more)

#     async def _meta_data_getter(self):
#         """
#         元の meta_data_getter() と同じロジックで、1ページ目のデータを取得する
#         """
#         retrial_num = 0
#         while True:
#             try:
#                 async with aiohttp.ClientSession() as session:
#                     async with session.get(self.endpoint_url, params=self.params, timeout=5) as response:
#                         print(response.url)
#                         if response.status == 200:
#                             data = await response.json()
#                             meta = data.get("meta", {})
#                             results = data.get("results", [])

#                             # ログ出力
#                             meta_data_str = "\n".join([f"{k}: {v}" for k, v in meta.items()])
#                             self.print_log(f"id:{self.id}\nMeta Data:\n{meta_data_str}")

#                             # 日本人著者抽出
#                             if self.only_japanese:
#                                 results = self.extract_japanese(results)
#                             return meta, results
#                         else:
#                             retrial_num += 1
#                             await asyncio.sleep(retrial_num)
#                             self.print_log(f"_meta_data_getter retrial_num:{retrial_num}, id:{self.id}, "
#                                            f"Status Code:{response.status}")
#                             if retrial_num > 8:
#                                 print("データなしと見なす")
#                                 return {}, []
#             except asyncio.TimeoutError:
#                 print("リクエストがタイムアウトしました。再試行します。")
#             except Exception as e:
#                 print("サーバーから遮断されたかもしれません。1秒待機します:", e)
#                 await asyncio.sleep(1)

#     async def _fetch_all_data_with_offset_pagination(self):
#         """
#         元の fetch_all_data_with_offset_pagination() と同じロジック:
#           total_pages = math.ceil(count/per_page) + 1
#           range(2, total_pages) でページを回す
#         非同期で各ページを取得 (asyncio.gather)
#         """
#         all_results = []
#         count = self.meta.get("count", 0)
#         per_page = self.meta.get("per_page", 200)
#         total_pages = math.ceil(count / per_page) + 1

#         pages = range(2, total_pages)  # 例: total_pages=6 -> [2,3,4,5]

#         async def fetch_page(page):
#             retrial_num = 0
#             while True:
#                 try:
#                     copied_params = self.params.copy()
#                     copied_params["page"] = page
#                     async with aiohttp.ClientSession() as session:
#                         async with session.get(self.endpoint_url, params=copied_params, timeout=5) as response:
#                             if response.status == 200:
#                                 data = await response.json()
#                                 results = data.get("results", [])
#                                 self.print_log(f"Fetched page {page} with {len(results)} results.")
#                                 if self.only_japanese:
#                                     results = self.extract_japanese(results)
#                                 return page, results
#                             else:
#                                 retrial_num += 1
#                                 await asyncio.sleep(retrial_num)
#                                 self.print_log(
#                                     f"[Offset] retrial:{retrial_num}, page:{page}, code:{response.status}"
#                                 )
#                                 if retrial_num > 8:
#                                     return page, []
#                 except asyncio.TimeoutError:
#                     print(f"page:{page} リクエストがタイムアウト。再試行します。")
#                 except Exception as e:
#                     print(f"page:{page} サーバーから遮断されたかもしれません:", e)
#                     await asyncio.sleep(1)

#         # 各ページを async でまとめて取得
#         tasks = [fetch_page(p) for p in pages]
#         pages_data = await asyncio.gather(*tasks)

#         # ページ番号順にソートしつつ、all_resultsに追加
#         pages_data_sorted = sorted(pages_data, key=lambda x: x[0])  # page番号でソート
#         for _, page_result in pages_data_sorted:
#             all_results.extend(page_result)

#         return all_results

#     async def _fetch_all_data_with_cursor_pagination(self):
#         """
#         元の fetch_all_data_with_cursor_pagination() と同じロジック
#         len(all_results) > 30000 の場合にbreak する
#         """
#         all_results = []
#         page = 1
#         # per_page は既に self.params にある想定
#         copied_params = self.params.copy()
#         if "page" in copied_params:
#             del copied_params["page"]

#         cursor = "*"
#         retrial_num = 0

#         while cursor:
#             copied_params["cursor"] = cursor
#             try:
#                 async with aiohttp.ClientSession() as session:
#                     async with session.get(self.endpoint_url, params=copied_params, timeout=5) as response:
#                         if response.status == 200:
#                             data = await response.json()
#                             results = data.get("results", [])
#                             self.print_log(f"Fetched page {page} with {len(results)} results.")
#                             if self.only_japanese:
#                                 results = self.extract_japanese(results)
#                             all_results.extend(results)

#                             if len(all_results) > 30000:
#                                 print("30000個以上:", self.meta)
#                                 break

#                             # 次のカーソルを取得してループ継続
#                             next_cursor = data.get("meta", {}).get("next_cursor", None)
#                             if not next_cursor:
#                                 break
#                             cursor = next_cursor
#                             page += 1
#                         else:
#                             retrial_num += 1
#                             await asyncio.sleep(retrial_num)
#                             print(f"[Cursor] retrial:{retrial_num}, page:{page}, code:{response.status}")
#                             if retrial_num > 8:
#                                 break
#             except asyncio.TimeoutError:
#                 print(f"[Cursor] page:{page} タイムアウト。再試行します。")
#             except Exception as e:
#                 print(f"[Cursor] page:{page} サーバーから遮断された可能性:", e)
#                 await asyncio.sleep(1)

#         return all_results

#     def extract_japanese(self, results_list):
#         """日本人著者だけを抽出するロジック（元と同じ）"""
#         japanese_results_list = []
#         for result in results_list:
#             if self.author_JP_checker(result):
#                 japanese_results_list.append(result)
#         return japanese_results_list

#     def author_JP_checker(self, data):
#         for authorship in data.get("authorships", []):
#             for institution in authorship.get("institutions", []):
#                 if institution.get("country_code") == "JP":
#                     return True
#         return False

#     def print_log(self, text):
#         if self.output_log:
#             print(text)
            
            
# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         start_time = time.time()
        
#         endpoint_url = "https://api.openalex.org/works"
#         params = {
#            "filter": "type:article,publication_year:>2020,cited_by_count:>50,authorships.institutions.country_code:JP",
#            "page": 1,
#            "per_page": 20,
#         }

#         # インスタンス生成
#         fetcher = OpenAlexPagenationDataFetcherAio(
#             endpoint_url=endpoint_url,
#             params=params,
#             id="aaaaaa",         # ダミーの著者ID
#             max_works=100,
#             only_japanese=False,
#             use_API_key=True
#         )

#         # 非同期でデータを全部取得
#         await fetcher.fetch_all()

#         # 結果を確認
#         print(fetcher.meta)
#         print(len(fetcher.all_results), "件取得")

#         # 処理時間の計測
#         end_time = time.time()
#         elapsed_time = end_time - start_time
#         hours = int(elapsed_time // 3600)
#         minutes = int((elapsed_time % 3600) // 60)
#         seconds = int(elapsed_time % 60)
#         formatted_time = f"{hours}時間{minutes}分{seconds}秒"
#         print("処理時間:", formatted_time)

#     # イベントループで実行
#     asyncio.run(main())