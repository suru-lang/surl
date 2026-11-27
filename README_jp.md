[English](README.md) | [日本語](README_jp.md)

# surl

日本語のプログラミング言語「[する](https://github.com/suru-lang/suru)」で書いた、HTTP と HTTPS の curl のようなコマンドです。[suru-lang/http](https://github.com/suru-lang/http) のクライアントの上に書いてあり、1つのバイナリになります。オプションは curl と同じ綴りで、終了コードも curl に合わせてあるので、curl を覚えた手やスクリプトでそのまま使えます。

段階を分けて作っています(計画: [#1](https://github.com/suru-lang/surl/issues/1))。この版では、方法・見出し・データを付けて要求を送り、本文を書き出せます。

## 作り方

[kumu](https://github.com/suru-lang/suru/blob/main/README_jp.md) で:

```sh
kumu 作る          # 出力/surl を作る
```

する 0.10.0 以上と、OpenSSL の開発用のファイルが要ります([suru-lang/http](https://github.com/suru-lang/http/blob/main/README_jp.md#クライアント) のクライアントと同じです)。

## 使い方

```sh
surl https://example.com/                 # 本文を標準出力へ
surl -o 印.png https://example.com/印.png  # ファイルへ(バイナリもそのまま)
surl -O https://example.com/a/印.png      # 印.png へ
surl -sSf https://example.com/none        # 404 なら何も出さず、終了コード 22
surl example.com                          # スキームを省くと http://
surl -d name=する https://example.com/post # フォームを POST
surl --json '{"a":1}' https://example.com/api
surl -X DELETE -H "Authorization: Bearer x" https://example.com/item/1
surl -I https://example.com/              # 見出しだけ
```

| オプション | 意味 |
|---|---|
| `-o 道`、`--output 道` | 本文を道に書く(`-` なら標準出力) |
| `-O`、`--remote-name` | 本文を URL の道の最後の部分の名前で書く |
| `-s`、`--silent` | 知らせを出さない |
| `-S`、`--show-error` | `-s` でも失敗は知らせる |
| `-f`、`--fail` | 状態が 400 以上なら本文を書かずに 22 で終わる |
| `--url URL` | 取る URL |
| `-X 方法`、`--request 方法` | 方法(GET・POST など) |
| `-H "名前: 値"`、`--header` | 見出しを足す(値のない `名前:` は既定の見出しを消す) |
| `-d データ`、`--data` | POST で送る(`@道` はファイル、`@-` は標準入力。改行は除く) |
| `--data-binary データ` | そのまま送る(`@道`・`@-` も) |
| `--data-raw データ` | `@` を特別に扱わずに送る |
| `--data-urlencode データ` | %XX にして送る(`内容`・`=内容`・`名前=内容`・`@道`・`名前@道`) |
| `--json データ` | JSON として送る(Content-Type と Accept を付ける) |
| `-G`、`--get` | データを URL の `?` の後ろに付けて GET する |
| `-I`、`--head` | HEAD して、状態行と見出しだけを書く |
| `-A 名前`、`--user-agent` | User-Agent |
| `-e URL`、`--referer` | Referer |
| `-b "a=1; b=2"`、`--cookie` | Cookie |
| `-u 利用者:合言葉`、`--user` | Basic 認証 |
| `-h`、`--help` | 使い方を出す |
| `-V`、`--version` | 版を出す |

| 終了コード | いつ |
|---|---|
| 0 | できた(`-f` がなければ、状態が 400 以上でも) |
| 1 | URL が http:// でも https:// でもない |
| 2 | 知らないオプション、値がない、URL がない |
| 6 | 主機の名前を引けない |
| 7 | つなげない |
| 8 | 答えが HTTP でない |
| 22 | `-f` で状態が 400 以上 |
| 23 | 書き出せない、`-O` の名前がない(新しい curl は代わりに `curl_response` に書きます) |
| 35 | TLS で失敗した |
| 56 | 受け取る途中で切れた |
| 60 | 証明書を確かめられない |

中身は する からも使えます。`取得内のコマンド実行する` は、`引数内の引数解釈する` で読んだ `設定` を受け取って、終了コードを結果にします。

```
「surl/引数」 を 読み込む
「surl/取得」 を 読み込む

始めする とは 以下の入出力手順です
  番 とは （（「-s」 と 「-o」 と 「a.html」 と 「https://example.com/」） を 引数内の引数解釈する） を 取得内のコマンド実行した 結果
  番 を 表示する
  以上です
始めする
```

## 決めたこと

### 引数

1. **オプションは curl と同じ綴り。** 短いオプションは `-sSf` のようにまとめて書け、値を取る短いオプションは `-o 名前` とも `-o名前` とも書けます。長いオプションは次の引数を値にします。`--` から後ろは全部 URL です。
2. **n 番目の `-o`・`-O` は n 番目の URL のもの。** ないものは標準出力に書きます(curl と同じ)。
3. **引数を読むのは純粋な関数。** `引数.suru` が引数のリストを `設定` にし、読めなければ `設定 の 誤り` に理由(最初の1つ)を入れます。試験を簡単にするためです。

### 取る

1. **本文はバイト列のまま、塊ずつ書く。** 文字列を通さないので、画像などのバイナリもそのまま出て、大きなファイルもメモリに全部は置きません。書くのは C の `fopen`・`fwrite`・`fflush` です(標準出力は `fdopen(1)`)。
2. **スキームがなければ http://。** curl と同じです。
3. **URL は順に取り、最初の失敗で止める。** 終了コードはその失敗のものです。
4. **`-o` のファイルは見出しが届いてから開く。** `-f` で状態が 400 以上なら、ファイルを作りません。

### 送る

1. **方法。** `-X` が一番です。なければ `-I` は HEAD、データがあれば POST(`-G` なら GET)、ほかは GET です。
2. **データは `&` でつなぐ。** `-d`・`--data-binary`・`--data-raw`・`--data-urlencode`・`--json` をそれぞれバイト列にして、curl と同じく `&` でつなぎます(`--json` だけなら、つながずに並べます)。`-d` はファイルの改行と復帰を除きます。`--data-urlencode` は空白を `+` にし、英数字と `- . _ ~` はそのままにします。
3. **オプションから既定の見出しを足す。** データがあれば `Content-Type: application/x-www-form-urlencoded`(`--json` なら `application/json` と `Accept: application/json`)。`-A`・`-e`・`-b`・`-u` は `User-Agent`・`Referer`・`Cookie`・`Authorization` です。`-H` で同じ名前を渡せば `-H` のほうを使い、`-H "名前:"` は http の既定の見出し(`Accept` など)を消します。
4. **`-b` はクッキーの文字列だけ。** curl は値に `=` がなければクッキーのファイルとして読みますが、surl はそのまま送ります。

### 終了コード

1. **番号は curl に合わせる。** 本体と http の失敗の文から決めます(たとえば `接続する` の失敗で、理由が名前のことなら 6、ほかは 7)。知らせは日本語で、curl と同じく番号を括弧に入れます: `surl: (7) 『127.0.0.1:1』につなげませんでした(Connection refused)`。
2. **`-k` は作らない。** http で決めたとおり、証明書の確かめを切る方法は作りません。

## 試験

```sh
kumu 試験
kumu 点検
```

`試験/` の試験は、引数を読むことと、同じプロセスのスレッドで立てた小さなサーバーから取ることを確かめます。CI では `surl` を作り、手元のサーバーを相手に、本文・終了コード・送るもの(方法・道・見出し・本文を、そのまま返すサーバー `.github/試験/こだま.py` で読み返す)が curl と同じになるかを Linux と macOS で確かめます。

## 今後の候補

次の段階は [#1](https://github.com/suru-lang/surl/issues/1) にあります: 見る(`-i`・`-v`・`-w` など)、転送をたどる(`-L`)、時間切れとやり直し、`kumu 導入` で入れる。

## ライセンス

[MIT](LICENSE)
