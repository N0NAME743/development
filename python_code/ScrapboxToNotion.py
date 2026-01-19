# タイトルからjsonの中身を検索
def search_from_title(title):
    for page in list_pages:
        if page["title"]==title:
            # print(page["lines"])
            return page["lines"]
        else:
            pass
# 変換のための関数
def image_(line):
    if "[https://gyazo.com/" in line:
        image = "![](https://i.gyazo.com/" + line.split("[https://gyazo.com/")[1].strip("]") + ".png)"
    else:
        image = line
    return image

def link_(line):
    if "https://youtu.be" in line or "https://www.youtube.com" in line:
        link_ = line
    elif "[http" in line:
        try:
            title = line.split(" ", 1)[1].strip("]")
            link = line.split(" ", 1)[0].strip("[")
            link_ = "[" + title + "](" + link + ")"
        except:
            # 例外のリンクはそのまま残す
            print(line)
            link_ = line
    else:
        link_ = line
    return link_

# 変換
def sb2md(page):
    list_md_ele = []
    for i in range(len(page)):
        list_ = []
        line = page[i]
        # スペース入りの行は飛ばす
        if len(line)!=0 and line[0]==" ":
            pass
        else:
            # 変換 lineを更新していく
            # 箇条書き
            line = line.replace('\t\t\t\t', '    - ')
            line = line.replace('\t\t\t', '  - ')
            line = line.replace('\t\t', '- ')
            # 見だし
            line = line.replace('\t', '## ')
            # 引用
            line = line.replace('>', '> ')
            # 画像
            line = image_(line)
            # リンク
            line = link_(line)
            list_.append(line)
            # コード
            if "code:" in line:
                list_.remove(line)
                line = '```' + line.split(":")[1]
                list_.append(line)
                j = 1
                while True:
                    code_ = page[i+j]
                    # コードの中身がスペースのみのとき
                    if code_==" ":
                        list_.append('```')
                        break 
                    elif len(code_)!=0 and code_[0]==" ":
                        code = code_.lstrip(" ")
                        list_.append(code)
                        j += 1
                    else:
                        list_.append('```')
                        break
            # tableはそのまま追加する
            if "table:" in line:
                list_.remove(line)
                j = 1
                while True:
                    table_ = page[i+j]
                    if len(table_)!=0 and table_[0]==" ":
                        code = table_.lstrip(" ")
                        list_.append(code)
                        j += 1
                    else:
                        break
        # list_の中身を追加する
        if len(list_)==1:
            list_md_ele.append(list_[0])
        else:
            for ele in list_:
                list_md_ele.append(ele)  
    # ページのタイトル
    title = list_md_ele[0]
    # 日付の下に1行空きを入れておく
    list_md_ele = list_md_ele[1:]
    list_md_ele.insert(1, '')

    return title, list_md_ele

# ファイルへ書き出し
def md2file(title , list_):
    title = title.replace("/", "")
    with open('markdown/{}.md'.format(title), 'w') as f:
        for d in list_:
            f.write("%s\n" % d)
    # print(title)

import json

json_open = open('noname743_20220601_041536.json', 'r')
json_load = json.load(json_open)
list_pages = json_load["1856"]

page = search_from_title("ページのタイトル")
title , list_ = sb2md(page)
md2file(title , list_)
