import os, csv, io, secrets, sqlite3
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Flask, request, session, redirect, url_for, abort, send_from_directory, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get("DATA_DIR",ROOT/"data")); UPLOADS=DATA/"uploads"
DATA.mkdir(parents=True,exist_ok=True); UPLOADS.mkdir(parents=True,exist_ok=True)
DB=DATA/"store.db"
app=Flask(__name__); app.secret_key=os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=32*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE","0")=="1")
ALLOWED={"pdf","zip","doc","docx","xls","xlsx","ppt","pptx","txt","png","jpg","jpeg","webp"}
PAYMENT_NAME=os.environ.get("PAYMENT_NAME","الكريمي"); PAYMENT_ACCOUNT=os.environ.get("PAYMENT_ACCOUNT","تُضاف بيانات الاستلام من إعدادات النشر"); PAYMENT_HOLDER=os.environ.get("PAYMENT_HOLDER","اسم المستفيد")
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def init_db():
 with db() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL);
  CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',category_id INTEGER,price INTEGER NOT NULL,cover TEXT,file_name TEXT,file_disk TEXT,published INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,FOREIGN KEY(category_id) REFERENCES categories(id));
  CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY,name TEXT NOT NULL,phone TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,order_no TEXT UNIQUE NOT NULL,customer_id INTEGER NOT NULL,total INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',receipt TEXT,transaction_ref TEXT,created_at TEXT NOT NULL,FOREIGN KEY(customer_id) REFERENCES customers(id));
  CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL,product_id INTEGER NOT NULL,product_name TEXT NOT NULL,price INTEGER NOT NULL,FOREIGN KEY(order_id) REFERENCES orders(id),FOREIGN KEY(product_id) REFERENCES products(id));
  INSERT OR IGNORE INTO categories(name) VALUES('كتب إلكترونية'),('قوالب ومستندات'),('دورات وتدريبات'),('أدوات وبرامج');""")
  pw=os.environ.get("ADMIN_PASSWORD",""); username=os.environ.get("ADMIN_USERNAME","admin").strip()
  if pw and len(pw)>=12: c.execute("INSERT OR IGNORE INTO admins(username,password_hash) VALUES(?,?)",(username,generate_password_hash(pw)))
init_db()
def csrf():
 if "csrf" not in session: session["csrf"]=secrets.token_urlsafe(24)
 return session["csrf"]
def verify_csrf():
 if not secrets.compare_digest(session.get("csrf",""),request.form.get("csrf","")): abort(400)
def admin_required(fn):
 @wraps(fn)
 def w(*a,**k):
  if not session.get("admin_id"): return redirect(url_for("admin_login"))
  return fn(*a,**k)
 return w
def store_upload(file,prefix):
 if not file or not file.filename: return None,None
 original=secure_filename(file.filename)
 if "." not in original or original.rsplit(".",1)[1].lower() not in ALLOWED: abort(400,"نوع الملف غير مسموح")
 ext=original.rsplit(".",1)[1].lower(); name=f"{prefix}_{secrets.token_hex(12)}.{ext}"
 file.save(UPLOADS/name); return name,original
def money(n): return f"{int(n):,} ر.ي"
STYLE="""*{box-sizing:border-box}body{margin:0;background:#f7f7fb;color:#172033;font-family:Tahoma,Arial,sans-serif;line-height:1.7}a{color:inherit;text-decoration:none}button,input,textarea,select{font:inherit}header{background:#101a3a;color:white;padding:13px 4%;display:flex;align-items:center;justify-content:space-between;gap:14px;position:sticky;top:0;z-index:4}.brand{font-size:22px;font-weight:900;color:white}.brand b{color:#f9a8d4}nav{display:flex;gap:14px;flex-wrap:wrap;font-size:14px}main{max-width:1100px;margin:24px auto;padding:0 16px;min-height:65vh}.hero{background:linear-gradient(120deg,#101a3a,#29205c 70%,#8c1c74);border-radius:22px;color:white;padding:35px 25px;text-align:center}.hero h1{font-size:clamp(25px,5vw,42px);margin:0 0 8px}.hero p{color:#fce7f3}.search{max-width:520px;margin:18px auto 0}.field{width:100%;border:1px solid #d9deea;border-radius:11px;padding:12px;background:white;margin:5px 0 12px}.btn{display:inline-block;background:#ec4899;color:white;border:0;border-radius:10px;padding:10px 16px;font-weight:bold;cursor:pointer}.btn.good{background:#087f5b}.btn.light{background:#fce7f3;color:#9d174d}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:18px 0}.card{background:white;border:1px solid #e8eaf1;border-radius:16px;padding:17px;box-shadow:0 5px 20px #18234a0a}.cover{width:100%;height:150px;object-fit:cover;border-radius:12px;background:#fce7f3}.price{font-weight:900;color:#b42372}.muted,.hint{color:#68738a;font-size:13px}.pill{display:inline-block;background:#fce7f3;color:#9d174d;border-radius:20px;padding:2px 10px;font-size:12px}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:space-between}.form{max-width:600px;margin:20px auto}.notice{padding:13px;border-radius:12px;background:#fff4e5;color:#854d0e;margin:12px 0}.success{background:#e8fff5;color:#066345}.error{background:#fff0f0;color:#9f1239}.table{width:100%;border-collapse:collapse;background:white}.table th,.table td{padding:10px;border-bottom:1px solid #e8eaf1;text-align:right;font-size:13px}.table th{background:#f8f8fc}.adminnav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.adminnav a{padding:8px 12px;border-radius:9px;background:#e9eaf2}.footer{text-align:center;padding:25px;color:#68738a;font-size:12px}.scroll{overflow:auto}@media(max-width:700px){header{align-items:flex-start;flex-direction:column}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.hero{padding:25px 15px}.card{padding:12px}}@media(max-width:430px){.grid{grid-template-columns:1fr}.cover{height:180px}}"""
def page(title,body):
 return f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#101a3a"><title>{title} | الشميري</title><style>{STYLE}</style></head><body><header><a class="brand" href="/">الشميري <b>للمنتجات الرقمية</b></a><nav><a href="/">الرئيسية</a><a href="/#products">المنتجات</a><a href="/track">متابعة طلب</a><a href="/help">المساعدة</a></nav></header><main>{body}</main><footer class="footer">© الشميري للمنتجات الرقمية — جميع الحقوق محفوظة</footer></body></html>'
@app.get("/")
def home():
 q=request.args.get("q","").strip()
 with db() as c:
  cats=c.execute("SELECT * FROM categories ORDER BY name").fetchall()
  ps=c.execute("SELECT p.*,c.name category FROM products p LEFT JOIN categories c ON c.id=p.category_id WHERE p.published=1 AND (p.name LIKE ? OR p.description LIKE ?) ORDER BY p.id DESC",(f"%{q}%",f"%{q}%")).fetchall()
 cards="".join(f'<article class="card"><a href="/product/{p["id"]}">{("<img class=cover src=/media/"+p["cover"]+">") if p["cover"] else "<div class=cover></div>"}<span class=pill>{p["category"] or "منتج رقمي"}</span><h3>{p["name"]}</h3><p class=muted>{p["description"][:110]}</p><div class=row><b class=price>{money(p["price"])}</b><span class=btn>التفاصيل</span></div></a></article>' for p in ps)
 cat_html=" ".join(f'<span class=pill>{x["name"]}</span>' for x in cats)
 return page("الرئيسية",f'<section class=hero><h1>كل ما تحتاجه من منتجات رقمية في مكان واحد</h1><p>كتب وأدلة وقوالب وأدوات رقمية — اطلب بسهولة واستلم ملفاتك بعد تأكيد التحويل</p><form class=search><input class=field name=q value="{q}" placeholder="ابحث عن كتاب أو قالب أو أداة"><button class=btn>بحث</button></form></section><h2 id=products>تسوق المنتجات الرقمية</h2><p>{cat_html}</p><section class=grid>{cards or "لا توجد منتجات منشورة حاليًا."}</section>')
@app.get("/product/<int:pid>")
def product(pid):
 with db() as c: p=c.execute("SELECT p.*,c.name category FROM products p LEFT JOIN categories c ON c.id=p.category_id WHERE p.id=? AND p.published=1",(pid,)).fetchone()
 if not p: abort(404)
 cover=f'<img class=cover src="/media/{p["cover"]}">' if p["cover"] else ""
 return page(p["name"],f'<div class="card form">{cover}<span class=pill>{p["category"] or "رقمي"}</span><h1>{p["name"]}</h1><p>{p["description"]}</p><p class=price>{money(p["price"])}</p><p class=hint>منتج رقمي قابل للتنزيل بعد اعتماد الدفع</p><a class=btn href="/checkout/{pid}">اطلب الآن</a></div>')
def checkout_form(p):
 return page("إتمام الطلب",f'<section class="card form"><h2>إتمام الطلب</h2><p>{p["name"]} — <b class=price>{money(p["price"])}</b></p><form method=post enctype=multipart/form-data><input type=hidden name=csrf value="{csrf()}"><label>الاسم الكامل</label><input class=field name=name required maxlength=100><label>رقم الهاتف للتواصل</label><input class=field name=phone required maxlength=30 inputmode=tel><div class=notice><b>بيانات التحويل عبر {PAYMENT_NAME}</b><br>اسم المستفيد: {PAYMENT_HOLDER}<br>رقم الحساب: {PAYMENT_ACCOUNT}<br>حوّل قيمة الطلب ثم أرفق الإيصال أو أدخل رقم العملية.</div><label>إيصال التحويل (اختياري إذا أدخلت رقم العملية)</label><input class=field type=file name=receipt accept=".jpg,.jpeg,.png,.pdf"><label>رقم العملية / إشعار التحويل</label><input class=field name=transaction_ref maxlength=100><button class=btn>إرسال الطلب</button></form></section>')
@app.route("/checkout/<int:pid>",methods=["GET","POST"])
def checkout(pid):
 with db() as c: p=c.execute("SELECT * FROM products WHERE id=? AND published=1",(pid,)).fetchone()
 if not p: abort(404)
 if request.method=="GET": return checkout_form(p)
 verify_csrf(); name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip(); ref=request.form.get("transaction_ref","").strip()
 if not name or not phone or (not ref and not (request.files.get("receipt") and request.files["receipt"].filename)): abort(400,"أدخل بياناتك وأرفق الإيصال أو رقم العملية")
 with db() as c:
  c.execute("INSERT INTO customers(name,phone,created_at) VALUES(?,?,?) ON CONFLICT(phone) DO UPDATE SET name=excluded.name",(name,phone,datetime.utcnow().isoformat()))
  customer=c.execute("SELECT id FROM customers WHERE phone=?",(phone,)).fetchone()
  receipt,_=store_upload(request.files.get("receipt"),"receipt"); no="SHM-"+secrets.token_hex(4).upper()
  cur=c.execute("INSERT INTO orders(order_no,customer_id,total,status,receipt,transaction_ref,created_at) VALUES(?,?,?,'pending',?,?,?)",(no,customer["id"],p["price"],receipt,ref,datetime.utcnow().isoformat()))
  c.execute("INSERT INTO order_items(order_id,product_id,product_name,price) VALUES(?,?,?,?)",(cur.lastrowid,pid,p["name"],p["price"]))
 return page("تم استلام الطلب",f'<div class="card form"><div class="notice success">تم استلام طلبك، وهو الآن قيد مراجعة الدفع.</div><h2>رقم الطلب: {no}</h2><p>احتفظ برقم الطلب ورقم هاتفك لمتابعة الحالة.</p><a class=btn href=/track>متابعة الطلب</a></div>')
@app.route("/track",methods=["GET","POST"])
def track():
 if request.method=="GET": return page("متابعة الطلب",f'<section class="card form"><h2>متابعة الطلب</h2><form method=post><input type=hidden name=csrf value="{csrf()}"><label>رقم الطلب</label><input class=field name=order_no required><label>رقم الهاتف المستخدم في الطلب</label><input class=field name=phone required><button class=btn>عرض الحالة</button></form></section>')
 verify_csrf()
 with db() as c:
  o=c.execute("SELECT o.*,cu.phone FROM orders o JOIN customers cu ON cu.id=o.customer_id WHERE o.order_no=? AND cu.phone=?",(request.form.get("order_no","").strip(),request.form.get("phone","").strip())).fetchone()
  items=c.execute("SELECT * FROM order_items WHERE order_id=?",(o["id"],)).fetchall() if o else []
 if not o: body='<div class="card form notice error">لم يتم العثور على الطلب. تحقق من الرقم والهاتف.</div>'
 else:
  status={"pending":"قيد مراجعة التحويل","paid":"تم تأكيد الدفع — التنزيل متاح","rejected":"تعذر اعتماد التحويل"}.get(o["status"],o["status"])
  links="".join(f'<p>{x["product_name"]} — {money(x["price"])} '+(f'<a class="btn good" href="/download/{x["id"]}">تنزيل الملف</a>' if o["status"]=="paid" else '<span class=muted>التنزيل غير متاح حتى تأكيد الدفع</span>')+'</p>' for x in items)
  body=f'<div class="card form"><h2>الطلب {o["order_no"]}</h2><div class=notice>{status}</div><b>{money(o["total"])}</b>{links}</div>'
 return page("حالة الطلب",body)
@app.get("/download/<int:item_id>")
def download(item_id):
 with db() as c: x=c.execute("SELECT p.file_disk,p.file_name,o.status FROM order_items i JOIN orders o ON o.id=i.order_id JOIN products p ON p.id=i.product_id WHERE i.id=?",(item_id,)).fetchone()
 if not x or x["status"]!="paid" or not x["file_disk"]: abort(403)
 return send_from_directory(UPLOADS,x["file_disk"],as_attachment=True,download_name=x["file_name"] or "digital-file")
@app.get("/media/<path:name>")
def media(name):
 if "/" in name or "\\" in name: abort(404)
 return send_from_directory(UPLOADS,name)
@app.get("/help")
def help_page(): return page("المساعدة",f'<div class="card form"><h2>المساعدة والتواصل</h2><p>للاستفسار عن الطلب أو التحويل، تواصل معنا مع ذكر رقم الطلب.</p><p>رقم التواصل: {os.environ.get("SUPPORT_PHONE","يُضاف رقم التواصل من إعدادات النشر")}</p><a class=btn href=/track>متابعة طلبك</a></div>')
def login_form(): return f'<section class="card form"><h2>دخول الإدارة</h2><form method=post><input type=hidden name=csrf value="{csrf()}"><input class=field name=username placeholder="اسم المستخدم" required><input class=field type=password name=password placeholder="كلمة المرور" required><button class=btn>دخول آمن</button></form><p class=hint>تُنشأ بيانات الدخول من متغيرات ADMIN_USERNAME وADMIN_PASSWORD في بيئة الاستضافة.</p></section>'
@app.route("/admin/login",methods=["GET","POST"])
def admin_login():
 if request.method=="POST":
  verify_csrf()
  with db() as c: a=c.execute("SELECT * FROM admins WHERE username=?",(request.form.get("username",""),)).fetchone()
  if a and check_password_hash(a["password_hash"],request.form.get("password","")):
   session.clear(); session["admin_id"]=a["id"]; session["csrf"]=secrets.token_urlsafe(24); return redirect("/admin")
  return page("دخول الإدارة",'<div class="notice error">بيانات الدخول غير صحيحة</div>'+login_form())
 return page("دخول الإدارة",login_form())
@app.get("/admin/logout")
def admin_logout(): session.clear(); return redirect("/")
@app.get("/admin")
@admin_required
def admin():
 with db() as c:
  stats=c.execute("SELECT COUNT(*) n,COALESCE(SUM(CASE WHEN status='paid' THEN total ELSE 0 END),0) sales,SUM(status='pending') pending FROM orders").fetchone()
  orders=c.execute("SELECT o.*,cu.name,cu.phone FROM orders o JOIN customers cu ON cu.id=o.customer_id ORDER BY o.id DESC LIMIT 100").fetchall()
  products=c.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
 rows="".join(f'<tr><td>{o["order_no"]}</td><td>{o["name"]}<br>{o["phone"]}</td><td>{money(o["total"])}</td><td>{o["status"]}</td><td>{o["transaction_ref"] or "—"} {"<a href=/admin/receipt/"+str(o["id"])+">الإيصال</a>" if o["receipt"] else ""}</td><td>'+(f'<form method=post action=/admin/order/{o["id"]}><input type=hidden name=csrf value="{csrf()}"><button class="btn good" name=status value=paid>تأكيد الدفع</button> <button class="btn light" name=status value=rejected>رفض</button></form>' if o["status"]=="pending" else "—")+'</td></tr>' for o in orders)
 prows="".join(f'<tr><td>{p["name"]}</td><td>{money(p["price"])}</td><td>{"منشور" if p["published"] else "مخفي"}</td><td><a href="/admin/product/{p["id"]}">تعديل</a> · <form style="display:inline" method=post action="/admin/publish/{p["id"]}"><input type=hidden name=csrf value="{csrf()}"><button class="btn light">تبديل النشر</button></form></td></tr>' for p in products)
 body=f'<div class=row><h1>لوحة إدارة الشميري</h1><a href=/admin/logout>تسجيل الخروج</a></div><div class=adminnav><a href=/admin>الطلبات والمنتجات</a><a href=/admin/product/new>إضافة منتج</a><a href=/admin/categories>التصنيفات</a><a href=/admin/export/orders>تصدير الطلبات CSV</a><a href=/admin/export/products>تصدير المنتجات CSV</a></div><div class=grid><div class=card>كل الطلبات<h2>{stats["n"] or 0}</h2></div><div class=card>بانتظار المراجعة<h2>{stats["pending"] or 0}</h2></div><div class=card>المبيعات المؤكدة<h2>{money(stats["sales"] or 0)}</h2></div></div><h2>الطلبات</h2><div class=scroll><table class=table><tr><th>الطلب</th><th>العميل</th><th>القيمة</th><th>الحالة</th><th>إثبات الدفع</th><th>الإجراء</th></tr>{rows}</table></div><h2>المنتجات</h2><div class=scroll><table class=table><tr><th>المنتج</th><th>السعر</th><th>النشر</th><th>الإدارة</th></tr>{prows}</table></div>'
 return page("الإدارة",body)
@app.post("/admin/order/<int:oid>")
@admin_required
def order_status(oid):
 verify_csrf(); status=request.form.get("status")
 if status not in ("paid","rejected"): abort(400)
 with db() as c: c.execute("UPDATE orders SET status=? WHERE id=?",(status,oid))
 return redirect("/admin")
@app.get("/admin/receipt/<int:oid>")
@admin_required
def receipt(oid):
 with db() as c: r=c.execute("SELECT receipt FROM orders WHERE id=?",(oid,)).fetchone()
 if not r or not r["receipt"]: abort(404)
 return send_from_directory(UPLOADS,r["receipt"],as_attachment=True)
@app.route("/admin/product/<pid>",methods=["GET","POST"])
@admin_required
def product_edit(pid):
 editing=pid!="new"
 with db() as c:
  p=c.execute("SELECT * FROM products WHERE id=?",(int(pid),)).fetchone() if editing else None
  cats=c.execute("SELECT * FROM categories ORDER BY name").fetchall()
 if editing and not p: abort(404)
 if request.method=="POST":
  verify_csrf(); name=request.form.get("name","").strip(); desc=request.form.get("description","").strip()
  try: price=int(request.form.get("price","0"))
  except: abort(400)
  if not name or price<0: abort(400)
  cat=request.form.get("category_id") or None; published=1 if request.form.get("published")=="1" else 0
  cover,_=store_upload(request.files.get("cover"),"cover"); disk,original=store_upload(request.files.get("digital_file"),"product")
  with db() as c:
   if editing: c.execute("UPDATE products SET name=?,description=?,category_id=?,price=?,published=?,cover=COALESCE(?,cover),file_disk=COALESCE(?,file_disk),file_name=COALESCE(?,file_name) WHERE id=?",(name,desc,cat,price,published,cover,disk,original,int(pid)))
   else:
    if not disk: abort(400,"ارفع الملف الرقمي للمنتج")
    c.execute("INSERT INTO products(name,description,category_id,price,cover,file_name,file_disk,published,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(name,desc,cat,price,cover,original,disk,published,datetime.utcnow().isoformat()))
  return redirect("/admin")
 opts="".join(f'<option value={x["id"]} {"selected" if p and p["category_id"]==x["id"] else ""}>{x["name"]}</option>' for x in cats)
 body=f'<section class="card form"><h2>{"تعديل منتج" if editing else "إضافة منتج جديد"}</h2><form method=post enctype=multipart/form-data><input type=hidden name=csrf value="{csrf()}"><label>اسم المنتج</label><input class=field name=name required value="{p["name"] if p else ""}"><label>الوصف</label><textarea class=field name=description rows=4>{p["description"] if p else ""}</textarea><label>التصنيف</label><select class=field name=category_id>{opts}</select><label>السعر بالريال اليمني</label><input class=field name=price type=number min=0 required value="{p["price"] if p else 500}"><label>صورة الغلاف</label><input class=field type=file name=cover accept="image/*"><label>الملف الرقمي {"(اتركه فارغًا للاحتفاظ بالملف الحالي)" if editing else ""}</label><input class=field type=file name=digital_file {"required" if not editing else ""}><label><input type=checkbox name=published value=1 {"checked" if not p or p["published"] else ""}> نشر المنتج</label><button class=btn>حفظ المنتج</button></form></section>'
 return page("إدارة المنتجات",body)
@app.post("/admin/publish/<int:pid>")
@admin_required
def publish(pid):
 verify_csrf()
 with db() as c: c.execute("UPDATE products SET published=1-published WHERE id=?",(pid,))
 return redirect("/admin")
@app.route("/admin/categories",methods=["GET","POST"])
@admin_required
def categories():
 if request.method=="POST":
  verify_csrf(); name=request.form.get("name","").strip()
  if name:
   with db() as c: c.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)",(name,))
  return redirect("/admin/categories")
 with db() as c: rows=c.execute("SELECT * FROM categories ORDER BY name").fetchall()
 return page("التصنيفات",f'<section class="card form"><h2>التصنيفات</h2><form method=post><input type=hidden name=csrf value="{csrf()}"><input class=field name=name placeholder="اسم التصنيف" required><button class=btn>إضافة</button></form><ul>{"".join("<li>"+x["name"]+"</li>" for x in rows)}</ul></section>')
@app.get("/admin/export/<kind>")
@admin_required
def export(kind):
 with db() as c:
  if kind=="orders": rows=c.execute("SELECT o.order_no,cu.name,cu.phone,o.total,o.status,o.transaction_ref,o.created_at FROM orders o JOIN customers cu ON cu.id=o.customer_id").fetchall()
  elif kind=="products": rows=c.execute("SELECT id,name,description,price,published,created_at FROM products").fetchall()
  else: abort(404)
 out=io.StringIO(); w=csv.writer(out)
 if rows: w.writerow(rows[0].keys()); w.writerows([tuple(x) for x in rows])
 res=make_response("\ufeff"+out.getvalue()); res.headers["Content-Type"]="text/csv; charset=utf-8"; res.headers["Content-Disposition"]=f"attachment; filename={kind}.csv"; return res
@app.errorhandler(413)
def too_large(_): return page("حجم الملف",'<div class="notice error">حجم الملف أكبر من الحد المسموح (32 ميجابايت).</div>'),413
@app.errorhandler(400)
def bad_request(e): return page("طلب غير صالح",f'<div class="notice error">{getattr(e,"description","الطلب غير صالح")}</div>'),400
@app.errorhandler(404)
def not_found(_): return page("غير موجود",'<div class=card>الصفحة غير موجودة.</div>'),404
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
