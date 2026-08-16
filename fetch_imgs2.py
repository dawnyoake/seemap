# -*- coding: utf-8 -*-
"""第二轮补抓:只处理 data.js 中还没有 img 的节点,放慢节奏避免 429"""
import json, os, re, sys, time, urllib.request

PROXY = "http://127.0.0.1:7897"
UA = "KeyGraphBot/1.0 (personal graph app)"
API = "https://graphql.anilist.co"
RAWFILE = r"C:\Users\14507\DevEcoStudioProjects\SeeMap\entry\src\main\resources\rawfile"
IMGS = os.path.join(RAWFILE, "imgs")

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
)

def graphql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(API, data=body,
        headers={"Content-Type": "application/json", "User-Agent": UA})
    for attempt in range(4):
        try:
            with opener.open(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            sys.stderr.write("  retry %s: %s\n" % (attempt, e))
            time.sleep(3)
    return None

def download(url, fname):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://anilist.co/"})
    try:
        with opener.open(req, timeout=30) as r:
            b = r.read()
        if len(b) < 2000:
            return False
        with open(fname, "wb") as f:
            f.write(b)
        return True
    except Exception:
        return False

CHAR_Q = """query($s:String){Character(search:$s){id name{full native} image{large}
  media(perPage:10){nodes{title{romaji native}}}}}"""
STAFF_Q = """query($s:String){Staff(search:$s){id name{full native} image{large}}}"""
MEDIA_Q = """query($s:String){Media(search:$s,type:ANIME){id title{romaji native} coverImage{large}}}"""

WORK_KEYS = {
    "CLANNAD": ["clannad"],
    "KANON": ["kanon", "カノン"],
    "AIR": ["air"],
    "リトルバスターズ!": ["little busters", "リトルバスターズ"],
}
MEDIA_SEARCH = {
    "CLANNAD": "CLANNAD",
    "KANON": "Kanon",
    "AIR": "AIR",
    "リトルバスターズ!": "Little Busters",
}
STAFF_ALT = {
    "國府田マリ子": ["國府田マリ子", "国府田マリ子"],
    "たみやすともえ": ["たみやすともえ", "民安ともえ"],
    "やなせなつみ": ["やなせなつみ", "柳瀬なつみ"],
    "すずきけいこ": ["すずきけいこ", "鈴木恵子"],
    "鴨ノ宮ゆう": ["鴨ノ宮ゆう", "鴨ノ宮ユウ"],
    "Lia": ["Lia"],
    "村田太志": ["村田太志"],
    "徳井青空": ["徳井青空"],
    "織田優成": ["織田優成"],
}

def safe_fname(node_id):
    return re.sub(r'[\\/:*?"<>|\s]', "", node_id.replace(":", "_"))

def main():
    src = open(os.path.join(RAWFILE, "data.js"), encoding="utf-8").read()
    a, b = src.index("{"), src.rindex("}") + 1
    data = json.loads(src[a:b])
    os.makedirs(IMGS, exist_ok=True)
    ok, still = 0, 0
    for node in data["nodes"]:
        if node.get("img"):
            continue
        nid, name, ntype = node["id"], node["name"], node["type"]
        url = None
        if ntype == "work":
            res = graphql(MEDIA_Q, {"s": MEDIA_SEARCH.get(name, name)})
            if res and res.get("data", {}).get("Media"):
                url = res["data"]["Media"]["coverImage"]["large"]
        elif ntype == "character":
            res = graphql(CHAR_Q, {"s": name})
            if res:
                ch = (res.get("data") or {}).get("Character")
                if ch and ch.get("name", {}).get("native") == name:
                    titles = " ".join([str((m.get("title") or {}).get("romaji", "") or "") + " " +
                                       str((m.get("title") or {}).get("native", "") or "")
                                       for m in (ch.get("media") or {}).get("nodes", [])]).lower()
                    keys = WORK_KEYS.get(node.get("work", ""), [])
                    if not keys or any(k in titles for k in keys):
                        url = ch["image"]["large"]
        elif ntype == "va":
            for sname in STAFF_ALT.get(name, [name]):
                res = graphql(STAFF_Q, {"s": sname})
                if res:
                    st = (res.get("data") or {}).get("Staff")
                    if st and (st.get("name", {}).get("native") == sname or st.get("name", {}).get("full") == sname):
                        url = st["image"]["large"]
                        break
        if url:
            fname = safe_fname(nid) + ".jpg"
            if download(url, os.path.join(IMGS, fname)):
                node["img"] = "imgs/" + fname
                ok += 1
        else:
            still += 1
        time.sleep(0.9)
    js = "// Key 四作 角色×声优 关系数据(动画版声优, 含简体别名, 含图片)\nwindow.KEY_GRAPH = " + \
         json.dumps(data, ensure_ascii=False) + ";\n"
    with open(os.path.join(RAWFILE, "data.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print("PASS2 DONE ok=%d still_missing=%d" % (ok, still))

if __name__ == "__main__":
    main()
