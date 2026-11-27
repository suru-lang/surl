# 試験の相手: 要求の方法・道・見出し(Host・Connection を除く)・本文をそのまま返す
# 「/redir/302?to=/x」は 302 と「Location: /x」を返す(本文は読んで捨てる)
#   python3 こだま.py 口番
import http.server,sys,urllib.parse
class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def h(self):
        n=int(self.headers.get("Content-Length",0)); body=self.rfile.read(n)
        if self.path.startswith("/redir/"):
            u=urllib.parse.urlsplit(self.path); code=int(u.path.split("/")[2])
            self.send_response(code); self.send_header("Location",urllib.parse.parse_qs(u.query)["to"][0]); self.send_header("Content-Length","2"); self.end_headers()
            if self.command!="HEAD": self.wfile.write(b"mv")
            return
        out=(self.command+" "+self.path+"\n"+"".join(f"{k}: {v}\n" for k,v in self.headers.items() if k.lower() not in("host","connection"))+"\n").encode()+body
        self.send_response(200); self.send_header("Content-Length",str(len(out))); self.send_header("X-Up","Yes"); self.end_headers()
        if self.command!="HEAD": self.wfile.write(out)
    do_GET=do_POST=do_PUT=do_DELETE=do_HEAD=do_PATCH=h
    def log_message(self,*a): pass
http.server.ThreadingHTTPServer(("127.0.0.1",int(sys.argv[1])),H).serve_forever()
