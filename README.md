[English](README.md) | [日本語](README_jp.md)

# surl

A curl-like command for HTTP and HTTPS, written in [Suru](https://github.com/suru-lang/suru), the Japanese programming language. It is built on the client of [suru-lang/http](https://github.com/suru-lang/http) and becomes one binary. The options are spelled as in curl, and the exit codes follow curl, so hands and scripts that know curl can use it as is.

It is being built in stages (plan: [#1](https://github.com/suru-lang/surl/issues/1)). This version can send requests with methods, headers and data, write the body, show the headers and timings, and follow redirects.

## Building

With [kumu](https://github.com/suru-lang/suru/blob/main/README.md):

```sh
kumu 作る          # makes 出力/surl
```

It needs Suru 0.10.0 or later and OpenSSL's development files (the same as the client of [suru-lang/http](https://github.com/suru-lang/http/blob/main/README.md#client)).

## Usage

```sh
surl https://example.com/                 # the body to standard output
surl -o 印.png https://example.com/印.png  # to a file (binary as it is)
surl -O https://example.com/a/印.png      # to 印.png
surl -sSf https://example.com/none        # nothing on 404, exit code 22
surl example.com                          # without a scheme, http://
surl -d name=する https://example.com/post # POST a form
surl --json '{"a":1}' https://example.com/api
surl -X DELETE -H "Authorization: Bearer x" https://example.com/item/1
surl -I https://example.com/              # headers only
surl -v https://example.com/              # what is sent and what comes back, on standard error
surl -s -o /dev/null -w '%{http_code} %{time_total}\n' https://example.com/
surl -L http://example.com/old            # follow redirects
```

| Option | Meaning |
|---|---|
| `-o 道`, `--output 道` | Write the body to the path (`-` is standard output) |
| `-O`, `--remote-name` | Write the body under the last part of the URL's path |
| `-s`, `--silent` | Print no messages |
| `-S`, `--show-error` | Print failures even with `-s` |
| `-f`, `--fail` | When the status is 400 or more, write no body and exit with 22 |
| `--url URL` | The URL to fetch |
| `-X 方法`, `--request 方法` | The method (GET, POST, …) |
| `-H "名前: 値"`, `--header` | Add a header (`名前:` with no value removes a default header) |
| `-d データ`, `--data` | Send with POST (`@道` is a file, `@-` standard input; newlines are removed) |
| `--data-binary データ` | Send as it is (`@道` and `@-` too) |
| `--data-raw データ` | Send without treating `@` specially |
| `--data-urlencode データ` | Send %XX-encoded (`内容`, `=内容`, `名前=内容`, `@道`, `名前@道`) |
| `--json データ` | Send as JSON (with Content-Type and Accept) |
| `-G`, `--get` | Put the data after `?` in the URL and GET |
| `-I`, `--head` | HEAD, and write only the status line and headers |
| `-A 名前`, `--user-agent` | User-Agent |
| `-e URL`, `--referer` | Referer |
| `-b "a=1; b=2"`, `--cookie` | Cookie |
| `-u 利用者:合言葉`, `--user` | Basic authentication |
| `-i`, `--include` | Write the status line and headers before the body |
| `-v`, `--verbose` | Show the request head (`> `) and the response head (`< `) on standard error |
| `-D 道`, `--dump-header 道` | Write the status line and headers to the path (`-` is standard output) |
| `-w 書式`, `--write-out 書式` | Write after the transfer (`%{http_code}`, `%{response_code}`, `%{size_download}`, `%{size_header}`, `%{time_total}`, `%{url_effective}`, `%{content_type}`, `%{method}`, `%{num_redirects}`) |
| `-L`, `--location` | Follow a 301, 302, 303, 307 or 308 that has a `Location` |
| `--max-redirs 数` | The most redirects to follow (50 by default, -1 for no limit) |
| `-h`, `--help` | Print the usage |
| `-V`, `--version` | Print the version |

| Exit code | When |
|---|---|
| 0 | Done (a status of 400 or more too, without `-f`) |
| 1 | The URL is not http:// or https:// |
| 2 | Unknown option, a missing value, no URL |
| 6 | The host name cannot be resolved |
| 7 | Cannot connect |
| 8 | The answer is not HTTP |
| 22 | `-f` and a status of 400 or more |
| 23 | Cannot write the output, or `-O` has no name (newer curl writes `curl_response` instead) |
| 35 | TLS failed |
| 47 | More redirects than `--max-redirs` |
| 56 | The connection broke while receiving |
| 60 | The certificate could not be verified |

The body itself can also be used from Suru: `取得内のコマンド実行する` takes the `設定` read by `引数内の引数解釈する` and gives the exit code.

```
「surl/引数」 を 読み込む
「surl/取得」 を 読み込む

始めする とは 以下の入出力手順です
  番 とは （（「-s」 と 「-o」 と 「a.html」 と 「https://example.com/」） を 引数内の引数解釈する） を 取得内のコマンド実行した 結果
  番 を 表示する
  以上です
始めする
```

## Decisions

### Arguments

1. **Options are spelled as in curl.** Short options can be put together, as in `-sSf`, and a short option that takes a value can be written as `-o name` or `-oname`. Long options take their value from the next argument. After `--`, everything is a URL.
2. **The n-th `-o` or `-O` goes with the n-th URL.** URLs without one write to standard output, as in curl.
3. **Reading the arguments is a pure function.** `引数.suru` turns the list of arguments into a `設定`, and when they cannot be read, `設定 の 誤り` holds the reason (the first one). This keeps the tests simple.

### Fetching

1. **The body is written as bytes, a chunk at a time.** It does not go through strings, so images and other binaries come out as they are, and large files are not held in memory. Writing uses C's `fopen`, `fwrite` and `fflush` (standard output is `fdopen(1)`).
2. **Without a scheme, http://.** As in curl.
3. **URLs are fetched in order, and it stops at the first failure.** The exit code is that failure's.
4. **The file for `-o` is opened after the headers arrive.** With `-f` and a status of 400 or more, no file is made.

### Sending

1. **The method.** `-X` comes first. Without it, `-I` is HEAD, data makes it POST (GET with `-G`), and otherwise GET.
2. **Data is joined with `&`.** Each `-d`, `--data-binary`, `--data-raw`, `--data-urlencode` and `--json` becomes bytes and they are joined with `&` (only `--json` pieces are put side by side), as in curl. `-d` removes newlines and carriage returns from files. `--data-urlencode` writes spaces as `+`, and keeps letters, digits and `- . _ ~`.
3. **Default headers from options.** Data adds `Content-Type: application/x-www-form-urlencoded` (`application/json` and `Accept: application/json` with `--json`). `-A`, `-e`, `-b` and `-u` add `User-Agent`, `Referer`, `Cookie` and `Authorization`. A header of the same name given with `-H` wins, and `-H "名前:"` removes a default header of http (such as `Accept`).
4. **`-b` is the cookie string only.** curl also reads a file of cookies when the value has no `=`; surl sends it as it is.

### Looking

1. **Headers are written as they arrived.** `-i`, `-I` and `-D` write the status line as received (`HTTP/1.1 200 OK`) and the header names in their original spelling, with CRLF, then a blank line, as curl does.
2. **`-v` shows the request exactly as sent.** The `> ` lines come from http's `要求頭文にする`, so they include the default headers. There are no `* ` lines yet (connection details), and the body is not shown.
3. **`-w`.** `\n`, `\t`, `\r` and `\\` are turned into the characters and `%%` into `%`. `%{time_total}` is seconds with six decimals, from sending the request to the end of the body. `%{num_redirects}` is the number of redirects followed, `%{url_effective}` the last URL, and `%{size_header}` counts the headers of every response. Unknown `%{…}` are left as they are, and `@file` is not read yet.

### Following redirects

1. **What is followed.** With `-L`, a 301, 302, 303, 307 or 308 response with a `Location` header is followed; its body is not read. Without `-L`, the redirect response itself is the answer (exit code 0). Going past `--max-redirs` is exit code 47.
2. **The method, as curl does.** A request that sends data (whatever `-X` says) becomes bodyless after 301 or 302, and every request but `-I` after 303; without `-X` it becomes GET, and with `-X` the method stays. 307 and 308 send the same method and body again. The data of `-G` was put in the first URL and is not added again.
3. **Location.** An absolute URL, `//host/path`, `/path`, `?query` and a relative path are read from the current URL. `.` and `..` in the path are sent as they are.
4. **Credentials stay with the host.** When the host changes, `-u` and the `Authorization` and `Cookie` of `-H` are not sent (there is no `--location-trusted`). `-b` is still sent.
5. **Every response head is shown.** `-i`, `-I`, `-D` and `-v` show the head of each response in order, as curl does; only the last body is written. `-O` takes its name from the first URL.

### Exit codes

1. **The numbers follow curl.** They are decided from the text of the failure of the core and of http (for example, a failure of `接続する` whose reason is about the name is 6, and otherwise 7). The messages are in Japanese, with the number in parentheses as in curl: `surl: (7) 『127.0.0.1:1』につなげませんでした(Connection refused)`.
2. **No `-k`.** As decided in http, there is no way to turn off certificate verification.

## Tests

```sh
kumu 試験
kumu 点検
```

The tests in `試験/` read arguments, and fetch from a small server started in a thread of the same process. CI also builds `surl` and checks, against local servers, that the body, the exit codes and what is sent (method, path, headers and body, read back from an echo server, `.github/試験/こだま.py`) are the same as curl's, on Linux and macOS.

## Future work

The next stages are in [#1](https://github.com/suru-lang/surl/issues/1): timeouts and retries, and installing with `kumu 導入`.

## License

[MIT](LICENSE)
