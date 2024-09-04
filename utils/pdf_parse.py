# -*-coding:utf-8 -*-

"""
@author: hanke
@date: 2024/9/1 16:07
"""

import fitz  # PyMuPDF
import re
import pandas as pd


def convert_pdf_to_excel(pdf_path, excel_path):
    doc = fitz.open(pdf_path)

    text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        text += page.get_text()

    text = text.replace("\xa0",' ')

    # todo 下面这段正则提取会有重复，后向可以优化
    # 正则表达式用于提取A类、B类和C类字段
    pattern_A = re.compile(r"(\d+)\s+(\w+)\s+(.+?)\s+(ACL|AAAI|ACM|IEEE|Springer|AUAI|Elsevier|IOS Press|PMLR|CSS|ICLR|MIT Press|JMLR|British Machine Vision \nAssociation|ICCL|ISCA|Morgan Kaufmann|Online Proceeding|KSI Research Inc|Wiley Blackwell|AI-FOR-SDGS|IFIP|RSS|USENIX|IEEE\/ACM|ACM\/IEEE|Wiley|IFIP\/IEEE|ACM\/USENIX|ISOC|KSI|FME)\s+(http[^\s]+)", re.DOTALL)
    pattern_B = re.compile(r"(\d+)\s+(\w+)\s+(.+?)\s+(ACL|AAAI|ACM|IEEE|Springer|AUAI|Elsevier|IOS Press|PMLR|CSS|ICLR|MIT Press|JMLR|British Machine Vision \nAssociation|ICCL|ISCA|Morgan Kaufmann|Online Proceeding|KSI Research Inc|Wiley Blackwell|AI-FOR-SDGS|IFIP|RSS|USENIX|IEEE\/ACM|ACM\/IEEE|Wiley|IFIP\/IEEE|ACM\/USENIX|ISOC|KSI|FME)\s+(http[^\s]+)", re.DOTALL)
    pattern_C = re.compile(r"(\d+)\s+(\w+)\s+(.+?)\s+(ACL|AAAI|ACM|IEEE|Springer|AUAI|Elsevier|IOS Press|PMLR|CSS|ICLR|MIT Press|JMLR|British Machine Vision \nAssociation|ICCL|ISCA|Morgan Kaufmann|Online Proceeding|KSI Research Inc|Wiley Blackwell|AI-FOR-SDGS|IFIP|RSS|USENIX|IEEE\/ACM|ACM\/IEEE|Wiley|IFIP\/IEEE|ACM\/USENIX|ISOC|KSI|FME)\s+(http[^\s]+)", re.DOTALL)

    # 提取 A 类部分
    sections_A = re.split(r"(?<=\n)[一二三四五六七八九十]*\s*、?\s*A类", text)
    # 提取 B 类部分
    sections_B = re.split(r"(?<=\n)[一二三四五六七八九十]*\s*、?\s*B类", text)
    # 提取 C 类部分
    sections_C = re.split(r"(?<=\n)[一二三四五六七八九十]*\s*、?\s*C类", text)

    results_A = []
    results_B = []
    results_C = []

    # 处理每一部分 A 类
    for section in sections_A:
        matches_A = pattern_A.findall(section)
        results_A.extend([{'序号': m[0], '刊物简称': m[1], '刊物全称': m[2].strip(), '出版社': m[3], '网址': m[4]} for m in matches_A])

    # 处理每一部分 B 类
    for section in sections_B:
        matches_B = pattern_B.findall(section)
        results_B.extend([{'序号': m[0], '刊物简称': m[1], '刊物全称': m[2].strip(), '出版社': m[3], '网址': m[4]} for m in matches_B])

    # 处理每一部分 C 类
    for section in sections_C:
        matches_C = pattern_C.findall(section)
        results_C.extend([{'序号': m[0], '刊物简称': m[1], '刊物全称': m[2].strip(), '出版社': m[3], '网址': m[4]} for m in matches_C])

    # 打印结果
    print("A 类:")
    for entry in results_A:
        print(entry)

    print("\nB 类:")
    for entry in results_B:
        print(entry)

    print("\nC 类:")
    for entry in results_C:
        print(entry)

    # Combine results into a single DataFrame
    all_results = results_A + results_B + results_C
    df = pd.DataFrame(all_results)

    # Remove duplicates
    df = df.drop_duplicates()

    # Save the DataFrame to an Excel file
    df.to_excel(excel_path, index=False)

    print(f"Results saved to {excel_path}")


def merge_excel(excel_path1, excel_path2, out_excel_path):
    # Load the Excel files
    ccf_df = pd.read_excel(excel_path1, sheet_name='会议')
    caai_df = pd.read_excel(excel_path2, sheet_name='会议')

    ccf_df['刊物简称_CCF'] = ccf_df['刊物简称'].str.strip()
    caai_df['刊物简称_CAAI'] = caai_df['刊物简称'].str.strip()
    ccf_df['刊物简称'] = ccf_df['刊物简称'].str.strip().str.lower()
    caai_df['刊物简称'] = caai_df['刊物简称'].str.strip().str.lower()

    # # Rename '刊物简称' in CAAI to distinguish it during the merge
    # caai_df.rename(columns={'刊物简称': '刊物简称_CAAI'}, inplace=True)
    #
    # # Merge the dataframes on the original '刊物简称' from CCF
    # merged_df = pd.merge(ccf_df, caai_df, left_on="刊物简称", right_on="刊物简称_CAAI", how="outer", suffixes=('_CCF', '_CAAI'))

    # # Merge the dataframes based on the "刊物简称" column
    merged_df = pd.merge(ccf_df, caai_df, on="刊物简称", how="outer", suffixes=('_CCF', '_CAAI'))

    # Find common entries
    common_entries = merged_df.dropna(subset=['序号_CCF', '序号_CAAI'])

    # Replace "刊物简称" with the value from "刊物简称_CAAI"
    common_entries['刊物简称'] = common_entries['刊物简称_CAAI']

    # 找到仅在CCF中的项
    ccf_only = merged_df[merged_df['序号_CAAI'].isna()].copy()
    ccf_only['刊物简称'] = ccf_only['刊物简称_CCF']

    # 找到仅在CAAI中的项
    caai_only = merged_df[merged_df['序号_CCF'].isna()].copy()
    caai_only['刊物简称'] = caai_only['刊物简称_CAAI']

    # Save results to Excel files
    # common_entries.to_excel('common_entries.xlsx', index=False)
    # Append caai_only content to common_entries
    final_entries = pd.concat([common_entries, ccf_only, caai_only], ignore_index=True)

    # Save the final result to an Excel file
    final_entries.to_excel(out_excel_path, index=False)
    # caai_only.to_excel('caai_only.xlsx', index=False)

    print("Final entries (including CAAI only content) and CCF only data have been saved to Excel files.")


if __name__ == '__main__':
    # 1. 加载 PDF 文件，将CCF和CAAI等级分类文章进行读取
    pdf_path = "../_data/中国计算机学会推荐国际学术会议和期刊目录-2022.pdf"  # 替换为你的PDF文件路径
    excel_path = "../_data/中国计算机学会推荐国际学术会议和期刊目录-2022.xlsx"  # Replace with your desired Excel file path
    pdf_path1 = "../_data/人工智能学会期刊和会议分类清单.pdf"  # 替换为你的PDF文件路径
    excel_path1 = "../_data/期刊和会议分类清单.xlsx"  # Replace with your desired Excel file path
    # convert_pdf_to_excel(pdf_path,excel_path)
    # convert_pdf_to_excel(pdf_path1, excel_path1)

    # 2. 对生成的excel文件进行合并, 并将结果保存到out_excel_path路径
    out_excel_path = 'final_entries.xlsx'
    # merge_excel(excel_path, excel_path1, out_excel_path)

    # 3. 随后人工对out_excel_path进行清理(去除相关期刊，并且整理正则没有提取出来内容，检查链接和全称)，得到out_excel_path1
    out_excel_path1 = 'final_entries_1.xlsx'

