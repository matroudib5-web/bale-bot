# ═══════════════════════════════════════════════════════════════
#  🩹 پچ باگ‌ها (بازنویسی توابع)
# ═══════════════════════════════════════════════════════════════

TARGET_FREE_ITEMS = ("carpet_bomb", "war_speech", "war_storm", "revive",
                     "god_shield", "invisible", "double_attack", "lock_on",
                     "revenge", "seize_power")

# ─── پچ ۱: پیشنهاد صلح حالا جنگ رو تموم می‌کنه ───
async def on_neg_resp(update, ctx, nid, acc):
    uid = update.effective_user.id
    conn = db()
    r = conn.execute("SELECT * FROM negs WHERE id=? AND to_id=?", (nid, uid)).fetchone()
    if not r:
        conn.close(); await update.message.reply_text("❌ درخواست پیدا نشد."); return
    r = dict(r)
    conn.execute("UPDATE negs SET status=? WHERE id=?",
        ("accepted" if acc else "rejected", nid))
    if acc and r["kind"] == "nap":
        add_nap(uid, r["from_id"], int(gget("turn","1"))+10)
    if acc and r["kind"] == "cancel_nap":
        cancel_nap(uid, r["from_id"])
    if acc and r["kind"] == "alliance":
        try:
            aid = int(r["payload"])
            conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
        except: pass
    if acc and r["kind"] == "peace":
        from_uid = r["from_id"]; to_uid = uid
        conn.execute("DELETE FROM wars WHERE (atk_uid=? AND def_uid=?) OR (atk_uid=? AND def_uid=?)",
            (from_uid, to_uid, to_uid, from_uid))
        conn.execute("UPDATE states SET war=0 WHERE user_id=?", (from_uid,))
        conn.execute("UPDATE states SET war=0 WHERE user_id=?", (to_uid,))
        fs = get_state(from_uid); ts = get_state(to_uid)
        if fs and ts:
            peace_msg = (f"☮️ *صلح میان {COUNTRIES[fs['country']]['n']} و "
                         f"{COUNTRIES[ts['country']]['n']}*\n\n"
                         f"دو کشور رسماً به مخاصمات پایان دادند.")
            add_news(int(gget("turn","1")), "peace", peace_msg)
            try: await ctx.bot.send_message(NEWS_CH, peace_msg, parse_mode="Markdown")
            except: pass
            try: await ctx.bot.send_message(from_uid, peace_msg, parse_mode="Markdown")
            except: pass
    conn.commit(); conn.close()
    msg = "✅ قبول" if acc else "❌ رد"
    await update.message.reply_text(f"درخواست: {msg}", reply_markup=kb_main())
    try: await ctx.bot.send_message(r["from_id"], f"📩 پاسخ درخواستت: {msg}")
    except: pass

# ─── پچ ۲: آیتم‌های بدون هدف ───
async def apply_item_effect(ctx, uid, item_key, target_uid=None):
    st = get_state(uid)
    if not st: return "❌ خطا"
    c = COUNTRIES[st["country"]]
    result = "✅"
    if item_key in TARGET_FREE_ITEMS:
        if item_key == "carpet_bomb":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], happiness=max(0, ps["happiness"]-10))
            result = "🔥 بمباران قالی — همه دشمنان آسیب دیدند."
        elif item_key == "war_speech":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], money=max(0, ps["money"]*0.5))
            result = "📢 نطق جنگی — ۵۰٪ پول همه به تو رسید."
        elif item_key == "war_storm":
            result = "🌪 طوفان جنگی — همه حملات دشمن عقب رانده شد."
        elif item_key == "revive":
            add_effect(uid, "revive", 999)
            result = "🔄 محافظت مرگ فعال شد."
        elif item_key == "god_shield":
            add_effect(uid, "shield", 60)
            result = "🛡 سپر جان — ۱ ساعت نامیرا."
        elif item_key == "invisible":
            add_effect(uid, "invisible", 30)
            result = "👻 نامرئی — ۳۰ دقیقه."
        elif item_key == "double_attack":
            add_effect(uid, "double_attack", 10)
            result = "⚡ دوبرابر حمله — ۱۰ نوبت."
        elif item_key == "lock_on":
            add_effect(uid, "lock_on", 10)
            result = "🎯 قفل روی حریف — ۱۰ نوبت."
        elif item_key == "revenge":
            add_effect(uid, "revenge", 999)
            result = "💀 انتقام فعال شد."
        elif item_key == "seize_power":
            add_effect(uid, "commander", 10)
            result = f"👑 {c['n']} ۱۰ نوبت فرمانده شد."
        add_news(st["turn"], "item", result)
        return result
    if item_key == "force_exile" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"🗳 {COUNTRIES[ts['country']]['n']} از بازی اخراج شد."
    elif item_key == "censor" and target_uid:
        add_effect(target_uid, "censored", 3)
        result = f"🤐 {COUNTRIES[get_state(target_uid)['country']]['n']} ۳ نوبت سانسور شد."
    elif item_key == "expose" and target_uid:
        result = f"🕵️ اطلاعات {COUNTRIES[get_state(target_uid)['country']]['n']} فاش شد."
    elif item_key == "force_ally" and target_uid:
        aid = get_user_alliance(uid)
        if not aid:
            conn = db()
            cur = conn.execute("INSERT INTO alliances(name,founder) VALUES(?,?)",
                (f"اتحاد {c['n']}", uid))
            aid = cur.lastrowid
            conn.execute("INSERT INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
            conn.commit(); conn.close()
        conn = db()
        conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, target_uid))
        conn.commit(); conn.close()
        result = f"🤝 {COUNTRIES[get_state(target_uid)['country']]['n']} به اتحاد اضافه شد."
    elif item_key == "plunder" and target_uid:
        ts = get_state(target_uid)
        if ts:
            half = ts["money"] // 2
            sset(target_uid, money=ts["money"] - half)
            sset(uid, money=st["money"] + half)
            result = f"💰 {fmt(half)} پول از دشمن غارت شد."
    elif item_key == "tsar_bomb" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"💣 بمب تزار — {COUNTRIES[ts['country']]['n']} نابود شد."
    elif item_key == "nuke_item" and target_uid:
        result = use_atomic(uid, target_uid)
    elif item_key == "bio_weapon" and target_uid:
        add_effect(target_uid, "no_attack", 5)
        result = f"☠️ {COUNTRIES[get_state(target_uid)['country']]['n']} ۵ نوبت نمی‌تونه حمله کنه."
    elif item_key == "ballistic" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"🚀 موشک بالستیک — {COUNTRIES[ts['country']]['n']} از بازی حذف شد."
    add_news(st["turn"], "item", result)
    return result

# ─── پچ ۳: هشدار به اعضای اتحاد در جنگ ───
_old_advance_wars = advance_wars

def advance_wars():
    conn = db()
    wars = conn.execute("SELECT * FROM wars").fetchall()
    conn.close()
    for w in wars:
        au = w["atk_uid"]; du = w["def_uid"]
        ast = get_state(au); dst = get_state(du)
        if not ast or not dst or dst.get("dead"):
            conn = db()
            conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
            conn.commit(); conn.close()
            continue
        t = w["turns"] - 1
        stage = w["stage"]
        if stage == "move" and t <= 0:
            my = calc_power(au, "attack")
            en = calc_power(du, "defense")
            aid_d = get_user_alliance(du)
            if aid_d:
                for m in get_alliance_members(aid_d):
                    if m != du and m != au:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            en += calc_power(m, "defense")
                            add_news(int(gget("turn","1")), f"ally_war_{m}",
                                f"{COUNTRIES[w['attacker']]['n']} به متحد تو "
                                f"{COUNTRIES[w['defender']]['n']} حمله کرد. "
                                f"بر اساس پیمان، در جنگ وارد شدی.")
            aid_a = get_user_alliance(au)
            if aid_a:
                for m in get_alliance_members(aid_a):
                    if m != au and m != du:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            my += calc_power(m, "attack")
                            add_news(int(gget("turn","1")), f"ally_war_{m}",
                                f"متحد تو {COUNTRIES[w['attacker']]['n']} به "
                                f"{COUNTRIES[w['defender']]['n']} حمله کرد. "
                                f"بر اساس پیمان، در جنگ وارد شدی.")
            battle_msg = (f"⚔️ نبرد میان {COUNTRIES[w['attacker']]['n']} و "
                          f"{COUNTRIES[w['defender']]['n']}\n"
                          f"قدرت حمله: {fmt(my)} — قدرت دفاع: {fmt(en)}")
            add_news(int(gget("turn","1")), "battle", battle_msg)
            if my > en:
                for u in get_army(au):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (int(u["count"]*0.85), u["id"]))
                    conn.commit(); conn.close()
                ds = get_state(du)
                if ds:
                    sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5,
                         soldiers=int(ds["soldiers"]*0.5))
                conn = db()
                conn.execute("UPDATE wars SET stage='resolve', turns=1 WHERE id=?",
                    (w["id"],))
                conn.commit(); conn.close()
                add_news(int(gget("turn","1")), "war",
                    f"🏆 {COUNTRIES[w['attacker']]['n']} در نبرد اولیه پیروز شد.")
                if calc_power(du, "defense") < my * 0.2:
                    conquer_country(None, au, du)
            else:
                for u in get_army(au):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (int(u["count"]*0.4), u["id"]))
                    conn.commit(); conn.close()
                conn = db()
                conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
                conn.commit(); conn.close()
                add_news(int(gget("turn","1")), "war",
                    f"💀 حمله {COUNTRIES[w['attacker']]['n']} شکست خورد.")
        elif stage == "resolve":
            ds = get_state(du)
            if ds:
                sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5)
                for u in get_army(du):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (int(u["count"]*0.5), u["id"]))
                    conn.commit(); conn.close()
                conquer_country(None, au, du)
            conn = db()
            conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
            conn.commit(); conn.close()

# ─── پچ ۴: تحویل پیام‌های هشدار اتحاد ───
async def deliver_pending(ctx):
    for p in all_players():
        uid = p["uid"]
        key = f"msg_read_{uid}"
        last_read = int(gget(key, "0") or 0)
        conn = db()
        rows = conn.execute(
            "SELECT * FROM news WHERE id>? AND (cat=? OR cat=? OR cat=? OR cat=? OR cat=?) ORDER BY id",
            (last_read, f"spy_ok_{uid}", f"spy_fail_{uid}",
             f"spy_caught_{uid}", f"ally_war_{uid}", f"conquest_{uid}")).fetchall()
        conn.close()
        for r in rows:
            try:
                if r["cat"].startswith("spy_ok_"):
                    await ctx.bot.send_message(uid,
                        f"✅ *جاسوسی موفق!*\n━━━━━━━━━━━━━━━━\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_fail_"):
                    await ctx.bot.send_message(uid,
                        f"❌ *جاسوس لو رفت!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_caught_"):
                    await ctx.bot.send_message(uid,
                        f"🚨 *هشدار امنیتی!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("ally_war_"):
                    await ctx.bot.send_message(uid,
                        f"⚠️ *هشدار اتحاد!*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                elif r["cat"].startswith("conquest_"):
                    await ctx.bot.send_message(uid,
                        f"💀 *اطلاعیه*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                last_read = r["id"]
            except: pass
        gset(key, str(last_read))

# ─── پچ ۵: on_text wrapper برای آیتم‌های بدون هدف ───
_old_on_text = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text in ITEM_FA and is_admin(uid):
        ik = ITEM_FA[text]
        if ik in TARGET_FREE_ITEMS:
            result = await apply_item_effect(ctx, uid, ik)
            await update.message.reply_text(result, reply_markup=kb_main())
            return
    return await _old_on_text(update, ctx)
# ═══════════════════════════════════════════════════════════════
#  🎨 کیبوردها
# ═══════════════════════════════════════════════════════════════
def kb_main():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 اقتصاد"),KeyboardButton("⚔️ ارتش")],
        [KeyboardButton("🔬 تحقیقات"),KeyboardButton("🏗️ پروژه‌ها")],
        [KeyboardButton("🏭 کارخونه‌ها"),KeyboardButton("🤝 دیپلماسی")],
        [KeyboardButton("📦 تجارت"),KeyboardButton("🎯 حمله")],
        [KeyboardButton("✈️ بمباران"),KeyboardButton("🕵️ جاسوسی")],
        [KeyboardButton("💵 مالیات"),KeyboardButton("🏛️ امور کشور")],
        [KeyboardButton("☢️ اتم"),KeyboardButton("📊 آمار کامل")]],resize_keyboard=True)

def kb_back():
    return ReplyKeyboardMarkup([[KeyboardButton("🔙 منو")]],resize_keyboard=True)

def kb_country():
    rows = []; row = []
    for k, c in COUNTRIES.items():
        ex_uid = find_country(k)
        if ex_uid:
            ex_st = get_state(ex_uid)
            if ex_st and not ex_st.get("dead"): continue
        row.append(KeyboardButton(f"{c['f']} {c['n']}"))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    return ReplyKeyboardMarkup(rows,resize_keyboard=True,one_time_keyboard=True)

def kb_gov():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👑 پادشاهی مطلقه"),KeyboardButton("👑 پادشاهی مشروطه")],
        [KeyboardButton("🗳️ جمهوری ریاستی"),KeyboardButton("🗳️ جمهوری پارلمانی")],
        [KeyboardButton("🚩 فاشیسم"),KeyboardButton("🚩 کمونیسم")],
        [KeyboardButton("⚙️ دیکتاتوری نظامی"),KeyboardButton("⚙️ دیکتاتوری شخصی")],
        [KeyboardButton("🕊️ دموکراسی لیبرال"),KeyboardButton("🕊️ دموکراسی اجتماعی")],
        [KeyboardButton("⚖️ تئوکراسی"),KeyboardButton("🚩 تک‌حزبی")]],
        resize_keyboard=True,one_time_keyboard=True)

def kb_army():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🪖 سرباز"),KeyboardButton("🛡️ تانک")],
        [KeyboardButton("✈️ جنگنده"),KeyboardButton("🚀 جت")],
        [KeyboardButton("🚢 کشتی"),KeyboardButton("🎯 موشک")],
        [KeyboardButton("💣 بمب‌افکن"),KeyboardButton("🛡️ پدافند")],
        [KeyboardButton("📋 خدمت اجباری")],[KeyboardButton("🔙 منو")]],
        resize_keyboard=True)

def kb_research():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔬🛡️ تانک"),KeyboardButton("🔬✈️ جنگنده")],
        [KeyboardButton("🔬🚀 جت"),KeyboardButton("🔬🚢 کشتی")],
        [KeyboardButton("🔬🎯 موشک"),KeyboardButton("🔬💣 بمب‌افکن")],
        [KeyboardButton("🔬🛡️ پدافند")],[KeyboardButton("🔙 منو")]],
        resize_keyboard=True)

def kb_projects():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🏭 صنعت"),KeyboardButton("⚡ انرژی")],
        [KeyboardButton("🎖️ نظامی"),KeyboardButton("🏥 اجتماعی")],
        [KeyboardButton("🌾 کشاورزی"),KeyboardButton("📜 سیاسی")],
        [KeyboardButton("🛣️ حمل‌ونقل")],[KeyboardButton("🔙 منو")]],
        resize_keyboard=True)

def kb_dip():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🤝 پیشنهاد اتحاد"),KeyboardButton("☮️ پیشنهاد صلح")],
        [KeyboardButton("⚔️ اعلام جنگ"),KeyboardButton("🤐 پیمان عدم تعرض")],
        [KeyboardButton("📜 بیانیه رسمی"),KeyboardButton("🚪 خروج از اتحاد")],
        [KeyboardButton("❌ لغو NAP"),KeyboardButton("📨 درخواست‌های من")],
        [KeyboardButton("🔙 منو")]],resize_keyboard=True)

def kb_trade():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 پول"),KeyboardButton("🍞 غذا")],
        [KeyboardButton("💧 آب"),KeyboardButton("⚙️ فولاد")],
        [KeyboardButton("🛢️ نفت"),KeyboardButton("🪨 زغال")],
        [KeyboardButton("👥 نیرو"),KeyboardButton("❌ هیچی")],
        [KeyboardButton("🔙 منو")]],resize_keyboard=True)

def kb_internal():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📢 سخنرانی"),KeyboardButton("🚔 سرکوب")],
        [KeyboardButton("🕵️ نظارت بر مردم")],[KeyboardButton("🔙 منو")]],
        resize_keyboard=True)

def kb_surv():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🕵️ نظارت +۱۰"),KeyboardButton("🕵️ نظارت -۱۰")],
        [KeyboardButton("🔙 منو")]],resize_keyboard=True)

def kb_bomb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🏭 بمباران کارخونه"),KeyboardButton("🔧 بمباران تجهیزات")],
        [KeyboardButton("💀 ترور فرمانده"),KeyboardButton("🛢️ بمباران پالایشگاه")],
        [KeyboardButton("🔙 منو")]],resize_keyboard=True)

def kb_fate():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔴 اعدام"),KeyboardButton("🟢 بخشش")],
        [KeyboardButton("🔒 حبس")]],resize_keyboard=True)

def kb_targets(exclude):
    ps = all_players(exclude); rows = []; row = []
    for p in ps:
        c = COUNTRIES[p["c"]]
        row.append(KeyboardButton(f"{c['f']} {c['n']}"))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows,resize_keyboard=True)

def kb_models(ck, cat, uid):
    tree = get_tree(ck, cat); rows = []; row = []
    for item in tree:
        row.append(KeyboardButton(item[0]))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows,resize_keyboard=True)

def kb_fact(uid):
    f = get_fact(uid); rows = []; row = []
    for x in f:
        p = PROJECTS.get(x["fkey"],{})
        row.append(KeyboardButton(p.get("n", x["fkey"])))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows,resize_keyboard=True)

# ═══════════════════════════════════════════════════════════════
#  🔒 چک عضویت
# ═══════════════════════════════════════════════════════════════
async def check_join(update, ctx):
    nj = []
    for ch in CHANNELS:
        try:
            m = await ctx.bot.get_chat_member(chat_id=ch["u"], user_id=update.effective_user.id)
            if m.status not in (ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                nj.append(ch)
        except: nj.append(ch)
    return nj

async def send_join(update):
    rows = [[InlineKeyboardButton(ch["l"],
        url=f"https://ble.ir/{ch['u'].lstrip('@')}")] for ch in CHANNELS]
    await update.message.reply_text("🔒 عضویت لازم:", reply_markup=InlineKeyboardMarkup(rows))
    await update.message.reply_text("بعد از عضویت:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("عضو شدم ✅")]], resize_keyboard=True))

# ═══════════════════════════════════════════════════════════════
#  📰 ارسال خبر به کانال
# ═══════════════════════════════════════════════════════════════
async def post_to_channel(ctx, text):
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"news ch: {e}")

# ═══════════════════════════════════════════════════════════════
#  🌍 سازمان ملل
# ═══════════════════════════════════════════════════════════════
UN_STATE = {"active": False, "phase": "idle", "turn": 0, "votes": {"yes": [], "no": []}}

async def start_un(ctx, turn):
    UN_STATE["active"] = True
    UN_STATE["phase"] = "discussion"
    UN_STATE["turn"] = turn
    UN_STATE["votes"] = {"yes": [], "no": []}
    for p in all_players():
        try:
            await ctx.bot.send_message(p["uid"],
                f"🌍 *سازمان ملل — نوبت {turn}*\n\n"
                f"جلسه فوق‌العاده آغاز شد. تمام کشورهای عضو به مدت ۵ دقیقه فرصت دارند "
                f"مواضع خود را اعلام کنند. هر پیامی که بنویسید برای تمام اعضا ارسال می‌شود.",
                parse_mode="Markdown", reply_markup=kb_back())
        except: pass
    add_news(turn, "un", f"🌍 سازمان ملل — جلسه فوق‌العاده نوبت {turn} آغاز شد.")
    asyncio.create_task(un_timer(ctx))

async def un_timer(ctx):
    await asyncio.sleep(300)
    if not UN_STATE["active"]: return
    UN_STATE["phase"] = "voting"
    for p in all_players():
        try:
            await ctx.bot.send_message(p["uid"],
                "🗳️ *رای‌گیری*\n\nآیا با تمدید ۵ دقیقه‌ای جلسه موافقید؟",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("✅ آره"), KeyboardButton("❌ نه")]
                ], resize_keyboard=True), parse_mode="Markdown")
        except: pass
    await asyncio.sleep(30)
    if not UN_STATE["active"]: return
    v = UN_STATE["votes"]
    if len(v["yes"]) >= len(v["no"]):
        UN_STATE["phase"] = "discussion"
        for p in all_players():
            try: await ctx.bot.send_message(p["uid"], "🌍 ۵ دقیقه تمدید شد.", reply_markup=kb_back())
            except: pass
        await asyncio.sleep(300)
    await end_un(ctx)

async def end_un(ctx):
    UN_STATE["active"] = False
    UN_STATE["phase"] = "idle"
    for p in all_players():
        try: await ctx.bot.send_message(p["uid"], "🌍 جلسه سازمان ملل پایان یافت.", reply_markup=kb_main())
        except: pass

async def on_un_message(update, ctx, text):
    if not UN_STATE["active"]: return False
    if UN_STATE["phase"] == "voting":
        uid = update.effective_user.id
        if text == "✅ آره":
            if uid not in UN_STATE["votes"]["yes"]: UN_STATE["votes"]["yes"].append(uid)
            await update.message.reply_text("✅", reply_markup=kb_back()); return True
        if text == "❌ نه":
            if uid not in UN_STATE["votes"]["no"]: UN_STATE["votes"]["no"].append(uid)
            await update.message.reply_text("❌", reply_markup=kb_back()); return True
    if UN_STATE["phase"] == "discussion":
        uid = update.effective_user.id
        st = get_state(uid)
        if st:
            msg = f"{COUNTRIES[st['country']]['f']} {COUNTRIES[st['country']]['n']}: {text}"
            for p in all_players():
                try: await ctx.bot.send_message(p["uid"], msg)
                except: pass
        return True
    return False

# ═══════════════════════════════════════════════════════════════
#  📝 دستورات پایه
# ═══════════════════════════════════════════════════════════════
async def cmd_start(update, ctx):
    if await check_join(update, ctx): await send_join(update); return
    uid = update.effective_user.id
    st = get_state(uid)
    if st and not st.get("dead"):
        await update.message.reply_text(render_dash(st), reply_markup=kb_main(), parse_mode="Markdown")
        return
    await update.message.reply_text(
        "🎖️ به جنگ جهانی دوم خوش آمدی!\n\n"
        f"📅 شروع: ۱ سپتامبر ۱۹۳۹\n"
        f"🔢 {TOTAL_TURNS} نوبت\n"
        f"⏰ هر نوبت: {TURN_MINUTES} دقیقه = ۱ روز بازی\n\n"
        "🌍 کشورت رو انتخاب کن 👇",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🎮 بازی جدید")]], resize_keyboard=True))

async def on_newgame(update, ctx):
    if await check_join(update, ctx): await send_join(update); return
    await update.message.reply_text("🌍 *کشورت رو انتخاب کن:*",
        reply_markup=kb_country(), parse_mode="Markdown")

async def on_country_pick(update, ctx):
    text = update.message.text.strip()
    if text not in CMAP: return
    uid = update.effective_user.id
    key = CMAP[text]
    existing = get_state(uid)
    if existing and not existing.get("dead"): return
    ex_uid = find_country(key)
    if ex_uid:
        ex_st = get_state(ex_uid)
        if ex_st and not ex_st.get("dead"):
            await update.message.reply_text("❌ این کشور قبلاً انتخاب شده!"); return
    c = COUNTRIES[key]
    conn = db()
    conn.execute("DELETE FROM players WHERE user_id=?", (uid,))
    conn.execute("DELETE FROM states WHERE user_id=?", (uid,))
    conn.execute("INSERT INTO players(user_id,country,gov,is_vip) VALUES(?,?,?,?)",
        (uid, key, c["gov"], 1 if uid in ADMIN_IDS else 0))
    conn.execute("""INSERT INTO states(user_id,turn,game_date,money,food,water,
        steel,oil,coal,manpower,last_turn) VALUES(?,1,?,?,?,?,?,?,?,?,?)""",
        (uid, "1939-09-01", c["m"], c["fo"], c["fo"]/2, c["s"], c["o"],
         c["c"], c["mp"], datetime.utcnow().isoformat()))
    conn.commit(); conn.close()
    init_fact(uid)
    ctx.user_data["wait"] = "gov"
    await update.message.reply_text(
        f"✅ {c['f']} *{c['n']}*\n\n👑 نظام حکومتی خود را انتخاب کن 👇",
        reply_markup=kb_gov(), parse_mode="Markdown")

async def on_gov_pick(update, ctx):
    if ctx.user_data.get("wait") != "gov": return
    text = update.message.text.strip()
    gmap = {
        "👑 پادشاهی مطلقه":"absolute_monarchy","👑 پادشاهی مشروطه":"constitutional_monarchy",
        "🗳️ جمهوری ریاستی":"presidential_republic","🗳️ جمهوری پارلمانی":"parliamentary_republic",
        "🚩 فاشیسم":"fascist","🚩 کمونیسم":"communism",
        "⚙️ دیکتاتوری نظامی":"military_dictatorship","⚙️ دیکتاتوری شخصی":"personal_dictatorship",
        "🕊️ دموکراسی لیبرال":"liberal_democracy","🕊️ دموکراسی اجتماعی":"social_democracy",
        "⚖️ تئوکراسی":"theocracy","🚩 تک‌حزبی":"single_party",
    }
    if text not in gmap: return
    uid = update.effective_user.id
    pset(uid, gov=gmap[text])
    ctx.user_data["wait"] = None
    st = get_state(uid)
    await update.message.reply_text(f"✅\n\n{render_dash(st)}",
        reply_markup=kb_main(), parse_mode="Markdown")

async def cmd_menu(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st or st.get("dead"):
        await cmd_start(update, ctx); return
    await update.message.reply_text(render_dash(st),
        reply_markup=kb_main(), parse_mode="Markdown")

async def on_joined(update, ctx):
    if await check_join(update, ctx):
        await update.message.reply_text("❌ هنوز عضو نشدی.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("عضو شدم ✅")]], resize_keyboard=True))
        return
    await update.message.reply_text("✅ عضویت تأیید شد!",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🎮 بازی جدید")]], resize_keyboard=True))

async def on_stats(update, ctx):
    uid = update.effective_user.id
    if not get_state(uid): return
    await update.message.reply_text(render_stats(uid),
        reply_markup=kb_back(), parse_mode="Markdown")

async def cmd_myid(update, ctx):
    await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def cmd_players(update, ctx):
    ps = all_players()
    if not ps:
        await update.message.reply_text("بازیکنی وجود ندارد."); return
    t = "🌍 *بازیکنان فعال*\n"
    for p in ps:
        c = COUNTRIES.get(p["c"], {})
        t += f"{c.get('f','?')} {c.get('n','?')}\n"
    await update.message.reply_text(t, parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
#  💰 اقتصاد / مالیات
# ═══════════════════════════════════════════════════════════════
async def on_eco(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    await update.message.reply_text(
        f"💰 *اقتصاد {COUNTRIES[st['country']]['n']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 پول: {fmt(st['money'])}\n"
        f"🍞 غذا: {fmt(st['food'])}\n"
        f"💧 آب: {fmt(st['water'])}\n"
        f"⚙️ فولاد: {fmt(st['steel'])}\n"
        f"🛢️ نفت: {fmt(st['oil'])}\n"
        f"🪨 زغال: {fmt(st['coal'])}\n"
        f"👥 نیرو: {fmt(st['manpower'])}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💵 مالیات: {st['tax']}%",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("💵 تغییر مالیات")],[KeyboardButton("🔙 منو")]],
            resize_keyboard=True),
        parse_mode="Markdown")

async def on_tax(update, ctx):
    ctx.user_data["wait"] = "tax"
    await update.message.reply_text("💵 عدد بین ۰ تا ۵۰ را بفرست:",
        reply_markup=kb_back())

# ═══════════════════════════════════════════════════════════════
#  ⚔️ ارتش
# ═══════════════════════════════════════════════════════════════
async def on_army(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    await update.message.reply_text(
        f"⚔️ *ارتش {COUNTRIES[st['country']]['n']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚔️ قدرت حمله: {fmt(calc_power(uid,'attack'))}\n"
        f"🛡️ قدرت دفاع: {fmt(calc_power(uid,'defense'))}\n"
        f"🪖 سرباز: {fmt(st['soldiers'])}\n"
        f"🛡 پدافند: {fmt(get_aa_power(uid))}",
        reply_markup=kb_army(), parse_mode="Markdown")

async def on_army_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"buy_{cat}"
    lines = [CAT_N[cat],"━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power = item[0], item[1]
        ok = (i == 0) or (name in researched)
        lines.append(f"{'✅' if ok else '🔒'} {name} — قدرت {power}")
    lines.append("\n👇 روی مدل مورد نظر بزن")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

async def on_soldier(update, ctx):
    ctx.user_data["wait"] = "soldier"
    await update.message.reply_text(
        "🪖 *خرید سرباز*\nقیمت هر سرباز: ۵۰💰 + ۱👥\n\nتعداد:",
        reply_markup=kb_back(), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
#  🔬 تحقیقات
# ═══════════════════════════════════════════════════════════════
async def on_research(update, ctx):
    await update.message.reply_text("🔬 *درخت تحقیقات*\nدسته را انتخاب کن 👇",
        reply_markup=kb_research(), parse_mode="Markdown")

async def on_research_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"research_{cat}"
    lines = [f"🔬 {CAT_N[cat]}","━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power, cost = item[0], item[1], item[2]
        if i == 0: lines.append(f"✅ {name} (از اول باز)")
        elif name in researched: lines.append(f"✅ {name} (قدرت {power})")
        else: lines.append(f"🔒 {name} — {cost}💰")
    lines.append("\n👇 روی مدل مورد نظر بزن")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
#  🏗️ پروژه‌ها
# ═══════════════════════════════════════════════════════════════
async def on_projects(update, ctx):
    await update.message.reply_text("🏗️ *پروژه‌های ملی*\nدسته را انتخاب کن 👇",
        reply_markup=kb_projects(), parse_mode="Markdown")

async def on_projects_cat(update, ctx, cat):
    uid = update.effective_user.id
    done = get_done_proj(uid); in_q = {p["pkey"] for p in get_projq(uid)}
    rows = []; row = []
    cat_fa = {"industry":"صنعت","energy":"انرژی","military":"نظامی",
              "social":"اجتماعی","agri":"کشاورزی","politics":"سیاسی","transport":"حمل‌ونقل"}
    lines = [f"🏗️ پروژه‌های {cat_fa.get(cat,cat)}","━━━━━━━━━━━━━━━━"]
    for pk, p in PROJECTS.items():
        if p["cat"] != cat: continue
        if pk in done: lines.append(f"✅ {p['n']}")
        elif pk in in_q: lines.append(f"🔨 {p['n']} (در حال ساخت)")
        else:
            lines.append(f"🆕 {p['n']} — {p['m']}💰 + {p['s']}⚙️")
            row.append(KeyboardButton(p["n"]))
            if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    ctx.user_data["screen"] = f"proj_{cat}"
    await update.message.reply_text("\n".join(lines),
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
#  🏭 کارخونه‌ها
# ═══════════════════════════════════════════════════════════════
async def on_fact(update, ctx):
    uid = update.effective_user.id
    lines = ["🏭 *کارخونه‌های شما*","━━━━━━━━━━━━━━━━"]
    for f in get_fact(uid):
        p = PROJECTS.get(f["fkey"],{})
        lines.append(f"{p.get('n', f['fkey'])} — سطح {f['level']}")
    lines.append("\n👇 برای ارتقا، روی کارخونه بزن")
    ctx.user_data["screen"] = "fact"
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_fact(uid), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
#  🏛️ امور کشور
# ═══════════════════════════════════════════════════════════════
async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    t = (f"🏛️ *امور کشور {COUNTRIES[st['country']]['n']}*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n")
    if st.get("protest"): t += f"\n🔥 *اعتراض فعال* ({st.get('protest_t',0)} نوبت)"
    await update.message.reply_text(t, reply_markup=kb_internal(), parse_mode="Markdown")

async def on_speech(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["money"] < 300:
        await update.message.reply_text("❌ ۳۰۰💰 لازمه."); return
    sset(uid, money=st["money"]-300)
    c = COUNTRIES[st["country"]]
    speech = (f"📢 رهبر {c['n']} در سخنرانی امروز خود خطاب به ملت گفت:\n\n"
              f"«ما در روزهای سرنوشت‌سازی قرار داریم. اتحاد و ایستادگی، "
              f"رمز پیروزی ماست. تاریخ این روزها را به یاد خواهد سپرد.»")
    add_news(st["turn"], "speech", speech)
    await post_to_channel(ctx, speech)
    await update.message.reply_text("📢 سخنرانی انجام شد و در کانال منتشر شد.",
        reply_markup=kb_main())

async def on_suppress(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st.get("protest"):
        await update.message.reply_text("❌ *اعتراضی برای سرکوب وجود ندارد.*",
            reply_markup=kb_main()); return
    if not pay(uid, money=500):
        await update.message.reply_text("❌ ۵۰۰💰 لازمه."); return
    sset(uid, suppress_cd=5, protest=0, protest_t=0,
         happiness=min(100, st["happiness"]+10))
    c = COUNTRIES[st["country"]]
    speech = generate_speech(uid, "suppress")
    msg = (f"🚔 *سرکوب اعتراضات در {c['n']}*\n\n"
           f"نیروهای امنیتی امروز تجمعات غیرقانونی را متفرق کردند.")
    add_news(st["turn"], "suppress", msg)
    await post_to_channel(ctx, msg)
    if speech:
        add_news(st["turn"], "speech", speech)
        await post_to_channel(ctx, speech)
    await update.message.reply_text(
        "🚔 سرکوب انجام شد!\n"
        "📈 کوتاه‌مدت: +۱۰ رضایت\n"
        "📉 بلندمدت: -۵ بعد ۵ نوبت",
        reply_markup=kb_main())

async def on_surv(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    await update.message.reply_text(
        f"🕵️ *نظارت بر مردم*\nالان: {st.get('surveillance',20)}%\n\n"
        f"✅ کاهش موفقیت جاسوس دشمن\n❌ کاهش رضایت\n❌ افزایش نارضایتی بلندمدت",
        reply_markup=kb_surv(), parse_mode="Markdown")

async def on_surv_change(update, ctx, delta):
    uid = update.effective_user.id
    st = get_state(uid)
    nv = max(0, min(100, st.get("surveillance",20)+delta))
    sset(uid, surveillance=nv)
    await update.message.reply_text(f"🕵️ نظارت: {nv}%", reply_markup=kb_surv())

# ═══════════════════════════════════════════════════════════════
#  🤝 دیپلماسی
# ═══════════════════════════════════════════════════════════════
async def on_dip(update, ctx):
    await update.message.reply_text("🤝 *دیپلماسی*\nگزینه مورد نظر را انتخاب کن 👇",
        reply_markup=kb_dip(), parse_mode="Markdown")

async def on_dip_action(update, ctx, kind):
    uid = update.effective_user.id
    if not all_players(exclude=uid):
        await update.message.reply_text("بازیکن دیگری وجود ندارد."); return
    ctx.user_data["dip_kind"] = kind
    ctx.user_data["wait"] = "dip_target"
    await update.message.reply_text("🎯 کشور هدف را انتخاب کن 👇",
        reply_markup=kb_targets(uid))

async def on_dip_target(update, ctx):
    if ctx.user_data.get("wait") != "dip_target": return
    text = update.message.text.strip()
    if text not in CMAP: return
    tk = CMAP[text]
    kind = ctx.user_data.get("dip_kind")
    uid = update.effective_user.id
    st = get_state(uid)
    tu = find_country(tk)
    if not tu:
        await update.message.reply_text("❌ این کشور بازیکن ندارد."); return
    c = COUNTRIES[tk]
    # اعلام جنگ
    if kind == "war":
        if is_in_same_alliance(uid, tu):
            await update.message.reply_text("❌ نمی‌تونی به متحدت حمله کنی!")
            ctx.user_data["wait"]=None; return
        if nap_active(uid, tu):
            until = get_nap(uid, tu)
            await update.message.reply_text(
                f"🤐 پیمان عدم تعرض تا نوبت {until} فعال است. نمی‌توانی حمله کنی.")
            ctx.user_data["wait"]=None; return
        conn = db()
        conn.execute("""INSERT INTO wars(attacker,defender,atk_uid,def_uid,
            stage,turns) VALUES(?,?,?,?,'move',1)""",
            (st["country"], tk, uid, tu))
        conn.commit(); conn.close()
        msg = (f"⚔️ *{COUNTRIES[st['country']]['n']} به {c['n']} اعلام جنگ کرد!*\n\n"
               f"نیروهای مسلح در مرزها آماده‌ی نبرد شده‌اند.")
        add_news(st["turn"], "war", msg)
        await post_to_channel(ctx, msg)
        key = f"speech_war_{uid}"
        if gget(key) != "done":
            gset(key, "done")
            speech = generate_speech(uid, "war")
            if speech:
                add_news(st["turn"], "speech", speech)
                await post_to_channel(ctx, speech)
        try:
            await ctx.bot.send_message(tu,
                f"⚔️ {COUNTRIES[st['country']]['n']} به تو اعلام جنگ کرد!")
        except: pass
        await update.message.reply_text(f"⚔️ جنگ با {c['n']} اعلام شد.",
            reply_markup=kb_main())
    # اتحاد
    elif kind == "ally":
        aid = get_user_alliance(uid)
        if not aid:
            conn = db()
            cur = conn.execute("INSERT INTO alliances(name,founder) VALUES(?,?)",
                (f"اتحاد {st['country']}", uid))
            aid = cur.lastrowid
            conn.execute("INSERT INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
            conn.commit(); conn.close()
        conn = db()
        conn.execute("INSERT INTO negs(from_id,to_id,kind,payload) VALUES(?,?,'alliance',?)",
            (uid, tu, str(aid)))
        conn.commit(); conn.close()
        try:
            await ctx.bot.send_message(tu,
                f"📩 *دعوت به اتحاد* از {COUNTRIES[st['country']]['n']}\n"
                f"برای پاسخ: 🤝 دیپلماسی → 📨 درخواست‌های من", parse_mode="Markdown")
        except: pass
        await update.message.reply_text("📤 دعوت ارسال شد.", reply_markup=kb_main())
    # NAP
    elif kind == "nap":
        conn = db()
        conn.execute("INSERT INTO negs(from_id,to_id,kind) VALUES(?,?,'nap')", (uid, tu))
        conn.commit(); conn.close()
        try:
            await ctx.bot.send_message(tu,
                f"📩 *پیشنهاد پیمان عدم تعرض* از {COUNTRIES[st['country']]['n']}\n"
                f"برای پاسخ: 🤝 دیپلماسی → 📨 درخواست‌های من", parse_mode="Markdown")
        except: pass
        await update.message.reply_text("📤 پیشنهاد NAP ارسال شد.", reply_markup=kb_main())
    # پیشنهاد صلح
    elif kind == "peace":
        conn = db()
        conn.execute("INSERT INTO negs(from_id,to_id,kind) VALUES(?,?,'peace')", (uid, tu))
        conn.commit(); conn.close()
        try:
            await ctx.bot.send_message(tu,
                f"📩 *پیشنهاد صلح* از {COUNTRIES[st['country']]['n']}",
                parse_mode="Markdown")
        except: pass
        await update.message.reply_text("📤 پیشنهاد صلح ارسال شد.", reply_markup=kb_main())
    # لغو NAP
    elif kind == "cancel_nap":
        if not nap_active(uid, tu):
            await update.message.reply_text("❌ پیمان فعالی وجود ندارد.")
            ctx.user_data["wait"]=None; return
        conn = db()
        conn.execute("INSERT INTO negs(from_id,to_id,kind) VALUES(?,?,'cancel_nap')", (uid, tu))
        conn.commit(); conn.close()
        try:
            await ctx.bot.send_message(tu,
                f"📩 *درخواست لغو پیمان عدم تعرض* از {COUNTRIES[st['country']]['n']}\n"
                f"برای پاسخ: 🤝 دیپلماسی → 📨 درخواست‌های من", parse_mode="Markdown")
        except: pass
        await update.message.reply_text("📤 درخواست لغو ارسال شد.", reply_markup=kb_main())
    ctx.user_data["wait"] = None

async def on_negs(update, ctx):
    uid = update.effective_user.id
    conn = db()
    rows = conn.execute("SELECT * FROM negs WHERE to_id=? AND status='pending'",
        (uid,)).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("📨 درخواست جدیدی نداری.", reply_markup=kb_main()); return
    lines = ["📨 *درخواست‌های دریافتی*","━━━━━━━━━━━━━━━━"]
    kbtns = []
    kind_fa = {"alliance":"اتحاد","nap":"عدم تعرض","peace":"صلح","cancel_nap":"لغو پیمان"}
    for r in rows:
        fs = get_state(r["from_id"])
        if not fs: continue
        lines.append(f"#{r['id']} — {COUNTRIES[fs['country']]['n']} → {kind_fa.get(r['kind'],r['kind'])}")
        kbtns.append([KeyboardButton(f"✅ قبول #{r['id']}"),
                      KeyboardButton(f"❌ رد #{r['id']}")])
    kbtns.append([KeyboardButton("🔙 منو")])
    await update.message.reply_text("\n".join(lines),
        reply_markup=ReplyKeyboardMarkup(kbtns,resize_keyboard=True), parse_mode="Markdown")

async def on_neg_resp(update, ctx, nid, acc):
    uid = update.effective_user.id
    conn = db()
    r = conn.execute("SELECT * FROM negs WHERE id=? AND to_id=?", (nid, uid)).fetchone()
    if not r: conn.close(); await update.message.reply_text("❌"); return
    r = dict(r)
    conn.execute("UPDATE negs SET status=? WHERE id=?",
        ("accepted" if acc else "rejected", nid))
    if acc and r["kind"] == "nap":
        add_nap(uid, r["from_id"], int(gget("turn","1"))+10)
    if acc and r["kind"] == "cancel_nap":
        cancel_nap(uid, r["from_id"])
    if acc and r["kind"] == "alliance":
        try:
            aid = int(r["payload"])
            conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
        except: pass
    conn.commit(); conn.close()
    msg = "✅ قبول" if acc else "❌ رد"
    await update.message.reply_text(msg, reply_markup=kb_main())
    try: await ctx.bot.send_message(r["from_id"], f"📩 پاسخ درخواستت: {msg}")
    except: pass

async def on_leave_alliance(update, ctx):
    uid = update.effective_user.id
    aid = get_user_alliance(uid)
    if not aid:
        await update.message.reply_text("تو اتحادی نیستی."); return
    conn = db()
    conn.execute("DELETE FROM allies WHERE user_id=?", (uid,))
    conn.commit(); conn.close()
    await update.message.reply_text("✅ از اتحاد خارج شدی.", reply_markup=kb_main())

async def on_cancel_nap(update, ctx):
    uid = update.effective_user.id
    ctx.user_data["dip_kind"] = "cancel_nap"
    ctx.user_data["wait"] = "dip_target"
    await update.message.reply_text("🎯 کدوم کشور رو می‌خوای لغو کنی؟", reply_markup=kb_targets(uid))

async def on_statement(update, ctx):
    ctx.user_data["wait"] = "statement"
    await update.message.reply_text("📜 متن بیانیه رسمی خود را بنویس:", reply_markup=kb_back())

# ═══════════════════════════════════════════════════════════════
#  📦 تجارت
# ═══════════════════════════════════════════════════════════════
async def on_trade(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    ctx.user_data["tr_step"] = "give"
    await update.message.reply_text(
        f"📦 *تجارت*\n💰{fmt(st['money'])} 🍞{fmt(st['food'])} ⚙️{fmt(st['steel'])}\n\n"
        f"*مرحله ۱:* چی می‌دی؟",
        reply_markup=kb_trade(), parse_mode="Markdown")

async def on_trade_give(update, ctx):
    if ctx.user_data.get("tr_step") != "give": return
    text = update.message.text.strip()
    m = {"💰 پول":"money","🍞 غذا":"food","💧 آب":"water","⚙️ فولاد":"steel",
         "🛢️ نفت":"oil","🪨 زغال":"coal","👥 نیرو":"manpower","❌ هیچی":"nothing"}
    if text not in m: return
    ctx.user_data["tr_give"] = m[text]
    ctx.user_data["tr_step"] = "give_amt"
    ctx.user_data["wait"] = "tr_amt"
    await update.message.reply_text("🔢 چند تا می‌دی؟", reply_markup=kb_back())

async def on_trade_want(update, ctx):
    if ctx.user_data.get("tr_step") != "want": return
    text = update.message.text.strip()
    m = {"💰 پول":"money","🍞 غذا":"food","💧 آب":"water","⚙️ فولاد":"steel",
         "🛢️ نفت":"oil","🪨 زغال":"coal","👥 نیرو":"manpower","❌ هیچی":"nothing"}
    if text not in m: return
    r = m[text]
    ctx.user_data["tr_want"] = r
    if r == "nothing":
        ctx.user_data["tr_want_amt"] = 0
        ctx.user_data["tr_step"] = "target"
        ctx.user_data["wait"] = "tr_target"
        await update.message.reply_text("🎯 طرف مقابل 👇",
            reply_markup=kb_targets(update.effective_user.id))
    else:
        ctx.user_data["tr_step"] = "want_amt"
        ctx.user_data["wait"] = "tr_amt"
        await update.message.reply_text("🔢 چقدر می‌خوای؟", reply_markup=kb_back())

async def on_trade_target(update, ctx):
    if ctx.user_data.get("wait") != "tr_target": return
    text = update.message.text.strip()
    if text not in CMAP: return
    tk = CMAP[text]
    uid = update.effective_user.id
    tu = find_country(tk)
    if not tu:
        await update.message.reply_text("❌"); return
    gr = ctx.user_data.get("tr_give","nothing")
    ga = ctx.user_data.get("tr_give_amt",0)
    wr = ctx.user_data.get("tr_want","nothing")
    wa = ctx.user_data.get("tr_want_amt",0)
    tst = get_state(tu)
    if wr != "nothing" and tst and tst.get(wr, 0) < wa:
        await update.message.reply_text(f"❌ {COUNTRIES[tk]['n']} مقدار کافی {wr} ندارد.")
        ctx.user_data["wait"]=None; ctx.user_data["tr_step"]=None; return
    conn = db()
    cur = conn.execute("INSERT INTO trades(from_id,to_id,gr,ga,wr,wa) VALUES(?,?,?,?,?,?)",
        (uid, tu, gr, ga, wr, wa))
    tid = cur.lastrowid
    conn.commit(); conn.close()
    st = get_state(uid)
    try:
        await ctx.bot.send_message(tu,
            f"📦 *پیشنهاد تجاری #{tid}*\nاز: {COUNTRIES[st['country']]['n']}\n"
            f"می‌ده: {ga} {gr}\nمی‌خواد: {wa} {wr}\n\n"
            f"پاسخ: `✅ قبول {tid}` یا `❌ رد {tid}`", parse_mode="Markdown")
    except: pass
    await update.message.reply_text("📤 فرستاده شد.", reply_markup=kb_main())
    ctx.user_data["wait"]=None; ctx.user_data["tr_step"]=None

async def on_trade_resp(update, ctx, tid, accept):
    uid = update.effective_user.id
    conn = db()
    r = conn.execute("SELECT * FROM trades WHERE id=? AND to_id=?", (tid, uid)).fetchone()
    if not r:
        conn.close(); await update.message.reply_text("❌ پیشنهاد پیدا نشد."); return
    r = dict(r)
    if r["status"] != "pending":
        conn.close(); await update.message.reply_text("❌ قبلاً پاسخ داده شده."); return
    conn.execute("UPDATE trades SET status=? WHERE id=?",
        ("accepted" if accept else "rejected", tid))
    conn.commit(); conn.close()
    if accept:
        from_id = r["from_id"]; to_id = r["to_id"]
        gr, ga, wr, wa = r["gr"], r["ga"], r["wr"], r["wa"]
        fs = get_state(from_id); ts = get_state(to_id)
        if fs and ts:
            if gr != "nothing" and ga > 0:
                sset(from_id, **{gr: fs.get(gr,0)-ga})
                sset(to_id, **{gr: ts.get(gr,0)+ga})
            if wr != "nothing" and wa > 0:
                sset(to_id, **{wr: ts.get(wr,0)-wa})
                sset(from_id, **{wr: fs.get(wr,0)+wa})
    msg = "✅ قبول" if accept else "❌ رد"
    await update.message.reply_text(f"پیشنهاد تجاری: {msg}", reply_markup=kb_main())
    try: await ctx.bot.send_message(r["from_id"], f"📦 پیشنهاد تجاری تو: {msg}")
    except: pass

# ═══════════════════════════════════════════════════════════════
#  🎯 حمله
# ═══════════════════════════════════════════════════════════════
async def on_attack(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["turn"] < ATTACK_UNLOCK:
        await update.message.reply_text(
            f"🔒 حمله تا نوبت {ATTACK_UNLOCK} غیرفعال است.")
        return
    if not all_players(exclude=uid):
        await update.message.reply_text("بازیکنی نیست."); return
    ctx.user_data["wait"] = "atk_target"
    await update.message.reply_text("🎯 کشور هدف 👇", reply_markup=kb_targets(uid))

async def on_attack_target(update, ctx):
    if ctx.user_data.get("wait") != "atk_target": return
    text = update.message.text.strip()
    if text not in CMAP: return
    tk = CMAP[text]
    uid = update.effective_user.id
    st = get_state(uid)
    tu = find_country(tk)
    if not tu:
        await update.message.reply_text("❌"); return
    if is_in_same_alliance(uid, tu):
        await update.message.reply_text("❌ نمی‌تونی به متحدت حمله کنی!")
        ctx.user_data["wait"]=None; return
    if nap_active(uid, tu):
        until = get_nap(uid, tu)
        await update.message.reply_text(
            f"🤐 پیمان عدم تعرض تا نوبت {until} فعال است.")
        ctx.user_data["wait"]=None; return
    if has_effect(tu, "invisible"):
        await update.message.reply_text("👻 دشمن نامرئی است! نمی‌تونی حمله کنی.")
        ctx.user_data["wait"]=None; return
    if not pay(uid, money=1000, oil=50):
        await update.message.reply_text("❌ نیاز: ۱۰۰۰💰 + ۵۰🛢️"); return
    sset(uid, war=1)
    conn = db()
    conn.execute("""INSERT INTO wars(attacker,defender,atk_uid,def_uid,
        stage,turns) VALUES(?,?,?,?,'move',1)""",
        (st["country"], tk, uid, tu))
    conn.commit(); conn.close()
    c = COUNTRIES[tk]
    msg = (f"⚔️ *{COUNTRIES[st['country']]['n']} به {c['n']} حمله کرد!*\n\n"
           f"نیروهای مسلح در حال حرکت به سمت مرزهای دشمن هستند.")
    add_news(st["turn"], "war", msg)
    await post_to_channel(ctx, msg)
    key = f"speech_war_{uid}"
    if gget(key) != "done":
        gset(key, "done")
        speech = generate_speech(uid, "war")
        if speech:
            add_news(st["turn"], "speech", speech)
            await post_to_channel(ctx, speech)
    try:
        await ctx.bot.send_message(tu,
            f"⚔️ *{COUNTRIES[st['country']]['n']} بهت حمله کرد!*\n"
            f"نبرد ۱ نوبت دیگر آغاز می‌شود.", parse_mode="Markdown")
    except: pass
    await update.message.reply_text(
        f"⚔️ حمله به {c['n']} آغاز شد.\n⏱️ ۱ نوبت حرکت، سپس نبرد.",
        reply_markup=kb_main())
    ctx.user_data["wait"]=None

# ═══════════════════════════════════════════════════════════════
#  ✈️ بمباران
# ═══════════════════════════════════════════════════════════════
async def on_bomb(update, ctx):
    await update.message.reply_text("✈️ *عملیات بمباران*\nنوع بمباران 👇",
        reply_markup=kb_bomb(), parse_mode="Markdown")

async def on_bomb_type(update, ctx, bt):
    uid = update.effective_user.id
    ctx.user_data["btype"] = bt
    ctx.user_data["wait"] = "bomb_target"
    await update.message.reply_text("🎯 کشور هدف 👇", reply_markup=kb_targets(uid))

async def on_bomb_target(update, ctx):
    if ctx.user_data.get("wait") != "bomb_target": return
    text = update.message.text.strip()
    if text not in CMAP: return
    tk = CMAP[text]
    uid = update.effective_user.id
    st = get_state(uid)
    tu = find_country(tk)
    if not tu:
        await update.message.reply_text("❌"); return
    if has_effect(tu, "invisible"):
        await update.message.reply_text("👻 نامرئیه!"); ctx.user_data["wait"]=None; return
    bt = ctx.user_data.get("btype","factory")
    # تعداد هواپیمای فرستاده شده
    forces = 100
    for u in get_army(uid):
        if u["category"] in ("bombers","fighters","jets"):
            forces += u["count"]
    success, msg = do_bombing(uid, tu, bt, forces)
    await update.message.reply_text(msg, reply_markup=kb_main())
    if success:
        # خبر به کانال
        kinds_fa = {"factory":"مواضع صنعتی","equip":"انبار تجهیزات",
                    "assassin":"فرماندهی","refinery":"پالایشگاه"}
        news_msg = (f"✈️ *بمباران {COUNTRIES[tk]['n']}*\n\n"
                    f"نیروی هوایی {COUNTRIES[st['country']]['n']} "
                    f"{kinds_fa.get(bt,'مواضع دشمن')} را بمباران کرد.")
        await post_to_channel(ctx, news_msg)
        try:
            await ctx.bot.send_message(tu,
                f"✈️ نیروی هوایی {COUNTRIES[st['country']]['n']} مواضع شما را بمباران کرد!")
        except: pass
    ctx.user_data["wait"]=None

# ═══════════════════════════════════════════════════════════════
#  🕵️ جاسوسی
# ═══════════════════════════════════════════════════════════════
async def on_spy(update, ctx):
    uid = update.effective_user.id
    if not all_players(exclude=uid):
        await update.message.reply_text("بازیکنی نیست."); return
    ctx.user_data["wait"] = "spy_target"
    await update.message.reply_text(
        "🕵️ *عملیات جاسوسی*\nهزینه: ۲۰۰💰\nزمان: ۱ تا ۳ نوبت\n\nهدف 👇",
        reply_markup=kb_targets(uid), parse_mode="Markdown")

async def on_spy_target(update, ctx):
    if ctx.user_data.get("wait") != "spy_target": return
    text = update.message.text.strip()
    if text not in CMAP: return
    tk = CMAP[text]
    uid = update.effective_user.id
    if not pay(uid, money=200):
        await update.message.reply_text("❌ ۲۰۰💰 لازمه."); return
    tu = find_country(tk)
    if not tu:
        await update.message.reply_text("❌"); return
    t = random.randint(1,3)
    conn = db()
    conn.execute("INSERT INTO spies(from_id,to_id,turns,status) VALUES(?,?,?,'pending')",
        (uid, tu, t))
    conn.commit(); conn.close()
    await update.message.reply_text(f"🕵️ جاسوس فرستاده شد. {t} نوبت طول می‌کشد.",
        reply_markup=kb_main())
    ctx.user_data["wait"]=None

# ═══════════════════════════════════════════════════════════════
#  ☢️ اتم
# ═══════════════════════════════════════════════════════════════
async def on_atomic(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["country"] not in ["germany","usa"] and gget("atomic_used") != "true":
        await update.message.reply_text("🔒 این پروژه در دسترس نیست."); return
    if st["turn"] < ATOMIC_UNLOCK:
        await update.message.reply_text(f"🔒 باز می‌شود در نوبت {ATOMIC_UNLOCK}."); return
    stage = st.get("atomic_stage", 0)
    if stage >= 3:
        await update.message.reply_text(
            f"☢️ *بمب اتمی آماده!*\nتعداد بمب: {st.get('atomic_bombs',0)}\n\n"
            f"برای استفاده: آیتم `بمب اتم` (فقط ادمین‌ها)",
            reply_markup=kb_main(), parse_mode="Markdown"); return
    s = ATOMIC_STAGES[stage]
    await update.message.reply_text(
        f"☢️ *پروژه اتمی*\nمرحله {stage}/3\n{s['n']}\n"
        f"⏱️ {s['t']} نوبت\n💰{s['m']} ⚙️{s['s']} 🛢️{s['o']}",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("☢️ شروع مرحله")],[KeyboardButton("🔙 منو")]],
            resize_keyboard=True), parse_mode="Markdown")

async def on_atomic_start(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    stage = st.get("atomic_stage", 0)
    if stage >= 3: return
    s = ATOMIC_STAGES[stage]
    if not pay(uid, money=s["m"], steel=s["s"], oil=s["o"]):
        await update.message.reply_text("❌ منابع کافی نیست."); return
    sset(uid, atomic_t=s["t"])
    await update.message.reply_text(f"✅ {s['n']} شروع شد!", reply_markup=kb_main())

# ═══════════════════════════════════════════════════════════════
#  🏆 سرنوشت رهبر
# ═══════════════════════════════════════════════════════════════
async def on_fate(update, ctx, fate):
    uid = update.effective_user.id
    st = get_state(uid)
    if fate == "execute":
        sset(uid, happiness=max(0, st["happiness"]-5))
        msg = "🔴 رهبر کشور فتح‌شده اعدام شد. (-۵ رضایت)"
    elif fate == "forgive":
        sset(uid, happiness=min(100, st["happiness"]+5))
        msg = "🟢 رهبر کشور فتح‌شده بخشیده شد. (+۵ رضایت)"
    else:
        msg = "🔒 رهبر کشور فتح‌شده به حبس ابد محکوم شد."
    add_news(st["turn"], "conquest", msg)
    await update.message.reply_text(msg, reply_markup=kb_main())

# ═══════════════════════════════════════════════════════════════
#  👑 دستورات ادمین
# ═══════════════════════════════════════════════════════════════
async def cmd_admin(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid): return
    ps = all_players()
    t = f"👑 *پنل ادمین*\nتعداد بازیکنان: {len(ps)}\n\n"
    for p in ps:
        c = COUNTRIES.get(p["c"], {})
        t += f"{c.get('f','?')} {c.get('n','?')} {'👑' if p['v'] else ''}\n"
    await update.message.reply_text(t, parse_mode="Markdown")

async def cmd_next_turn(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid): return
    advance_wars()
    for p in all_players():
        process_turn(p["uid"])
    gset("turn", int(gget("turn","1"))+1)
    await update.message.reply_text("⏭️ نوبت انجام شد.")

async def cmd_give(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid): return
    parts = update.message.text.split()
    if len(parts) < 4: return
    cn, field, amt = parts[1], parts[2], parts[3]
    fm = {"پول":"money","غذا":"food","آب":"water","فولاد":"steel",
          "نفت":"oil","زغال":"coal","نیرو":"manpower","سرباز":"soldiers"}
    if field not in fm:
        await update.message.reply_text("❌ فیلد نامعتبر."); return
    ck = CFA.get(cn)
    if not ck:
        await update.message.reply_text("❌ کشور پیدا نشد."); return
    tu = find_country(ck)
    if not tu:
        await update.message.reply_text("❌ بازیکن ندارد."); return
    st = get_state(tu)
    sset(tu, **{fm[field]: st.get(fm[field],0)+float(amt)})
    await update.message.reply_text(f"✅ {amt} {field} به {cn} داده شد.")

async def cmd_info(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid): return
    t = update.message.text.strip()
    if not t.startswith("اطلاعات "): return
    cn = t.replace("اطلاعات ","").strip()
    ck = CFA.get(cn)
    if not ck:
        await update.message.reply_text("❌ کشور پیدا نشد."); return
    tu = find_country(ck)
    if not tu:
        await update.message.reply_text("❌ بازیکن ندارد."); return
    await update.message.reply_text(render_stats(tu), parse_mode="Markdown")

async def cmd_vip(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid): return
    t = update.message.text.strip()
    if not t.endswith(" ویژه"): return
    cn = t[:-5].strip()
    ck = CFA.get(cn)
    if not ck:
        await update.message.reply_text("❌ کشور پیدا نشد."); return
    tu = find_country(ck)
    if not tu:
        await update.message.reply_text("❌ بازیکن ندارد."); return
    set_vip(tu, 1)
    await update.message.reply_text(f"👑 {cn} ویژه شد!")

async def cmd_item(update, ctx):
    uid = update.effective_user.id
    if not is_admin(uid): return
    parts = update.message.text.split()
    if len(parts) < 4 or parts[0] != "هدیه" or parts[1] != "آیتم": return
    cn = parts[2]
    item_name = " ".join(parts[3:])
    if item_name not in ITEM_FA:
        await update.message.reply_text("❌ آیتم نامعتبر."); return
    ck = CFA.get(cn)
    if not ck:
        await update.message.reply_text("❌ کشور پیدا نشد."); return
    tu = find_country(ck)
    if not tu:
        await update.message.reply_text("❌ بازیکن ندارد."); return
    ik = ITEM_FA[item_name]
    result = await apply_item_effect(ctx, tu, ik)
    await update.message.reply_text(f"✅ {item_name} به {cn}:\n{result}")

# ═══════════════════════════════════════════════════════════════
#  📨 ارسال پیام‌های جاسوسی معلق
# ═══════════════════════════════════════════════════════════════
async def deliver_pending(ctx):
    for p in all_players():
        uid = p["uid"]
        key = f"spy_read_{uid}"
        last_read = int(gget(key, "0") or 0)
        conn = db()
        rows = conn.execute(
            "SELECT * FROM news WHERE id>? AND (cat=? OR cat=? OR cat=?) ORDER BY id",
            (last_read, f"spy_ok_{uid}", f"spy_fail_{uid}",
             f"spy_caught_{uid}")).fetchall()
        conn.close()
        for r in rows:
            try:
                if r["cat"].startswith("spy_ok_"):
                    await ctx.bot.send_message(uid,
                        f"✅ *جاسوسی موفق!*\n━━━━━━━━━━━━━━━━\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_fail_"):
                    await ctx.bot.send_message(uid,
                        f"❌ *جاسوس لو رفت!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_caught_"):
                    await ctx.bot.send_message(uid,
                        f"🚨 *هشدار امنیتی!*\n{r['text']}",
                        parse_mode="Markdown")
                last_read = r["id"]
            except: pass
        gset(key, str(last_read))

# ═══════════════════════════════════════════════════════════════
#  💰 درآمد هر ۵ ثانیه
# ═══════════════════════════════════════════════════════════════
async def fast_income(ctx):
    if gget("season_ended") == "true": return
    for p in all_players():
        try:
            st = get_state(p["uid"])
            if not st or st.get("dead"): continue
            c = COUNTRIES[st["country"]]
            mult = 2.0 if is_vip(p["uid"]) else 1.0
            tm = st["tax"] / 20.0
            sset(p["uid"],
                money=st["money"] + (c["bm"]*tm*mult)/360,
                food=st["food"] + (c["bf"]*mult)/360,
                water=st["water"] + (c["bf"]*0.5*mult)/360,
                steel=st["steel"] + (c["bs"]*mult)/360,
                oil=st["oil"] + (c["bo"]*mult)/360,
                coal=st["coal"] + (c["bc"]*mult)/360,
                manpower=st["manpower"] + (50*mult)/360)
        except Exception as e:
            log.warning(f"fast: {e}")

# ═══════════════════════════════════════════════════════════════
#  🕐 نوبت خودکار (هر ۳۰ دقیقه)
# ═══════════════════════════════════════════════════════════════
async def auto_turn(ctx):
    if gget("season_ended") == "true": return
    # ۱. پیشرفت جنگ‌ها
    advance_wars()
    # ۲. نوبت همه بازیکنان
    players = all_players()
    nt = int(gget("turn","1")) + 1
    gset("turn", nt)
    for p in# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — همه اخبار هر نوبت، قاطی هم
# ═══════════════════════════════════════════════════════════════

async def news_post(ctx, title, body=""):
    if body:
        text = f"📰 *{title}*\n━━━━━━━━━━━━━━━━\n{body}"
    else:
        text = f"📰 *{title}*"
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"news ch: {e}")

_old_auto_turn_all = auto_turn

async def auto_turn(ctx):
    if gget("season_ended") == "true": return
    # ۱. جنگ‌ها
    advance_wars()
    # ۲. همه بازیکن‌ها
    players = all_players()
    nt = int(gget("turn","1")) + 1
    gset("turn", nt)
    # لیست همه خبرها
    news_items = []
    for p in players:
        try:
            res = process_turn(p["uid"])
            if not res: continue
            if res["ev"]:
                for e in res["ev"]:
                    news_items.append(("hist", e))
            t = f"📅 *نوبت {nt}* — {fmt_date(parse_date(res['date']))}\n"
            if res["ev"]:
                for e in res["ev"]:
                    t += f"• {e}\n"
            await ctx.bot.send_message(p["uid"], t,
                parse_mode="Markdown", reply_markup=kb_main())
        except Exception as e:
            log.warning(f"turn {p['uid']}: {e}")
    # ۳. خبرهای عمومی این نوبت
    conn = db()
    public_cats = ("war","battle","conquest","protest","suppress",
                   "un","statement","item","holocaust","peace",
                   "conscription","bomb")
    rows = conn.execute(
        f"SELECT * FROM news WHERE turn>=? AND cat IN ({','.join('?'*len(public_cats))}) ORDER BY id",
        (nt-2, *public_cats)).fetchall()
    conn.close()
    seen = set()
    for r in rows:
        key = r["text"][:50]
        if key in seen: continue
        seen.add(key)
        news_items.append((r["cat"], r["text"]))
    # ۴. خبر سرگرمی — هر نوبت
    news_items.append(("fun", random.choice(RANDOM_NEWS).format(n=random.randint(10, 500))))
    # ۵. ارسال همه به کانال تو یه پست
    if news_items:
        # تاریخ فعلی
        try:
            any_st = get_state(players[0]["uid"]) if players else None
            date_str = fmt_date(parse_date(any_st["game_date"])) if any_st else "—"
        except: date_str = "—"
        lines = [
            f"📰 *WORLD WAR NEWS — نوبت {nt}*",
            f"🗓️ {date_str}",
            "━━━━━━━━━━━━━━━━",
        ]
        cat_emoji = {
            "hist":"📜","war":"⚔️","battle":"🎯","conquest":"🏆",
            "protest":"🔥","suppress":"🚔","un":"🌍","statement":"📢",
            "item":"🎁","holocaust":"⚫","peace":"☮️",
            "conscription":"📋","bomb":"✈️","fun":"🎭",
        }
        for cat, txt in news_items:
            em = cat_emoji.get(cat, "•")
            lines.append(f"{em} {txt}")
        full = "\n".join(lines)
        # چک طول پیام
        if len(full) > 4000:
            full = full[:3900] + "\n...(ادامه در کانال)"
        try:
            await ctx.bot.send_message(NEWS_CH, full, parse_mode="Markdown")
        except Exception as e:
            log.warning(f"news: {e}")
    # ۶. اتم باز شد
    if nt == ATOMIC_UNLOCK:
        try:
            await ctx.bot.send_message(NEWS_CH,
                "☢️ *پروژه اتمی*\n\nپروژه منهتن امروز رسماً آغاز شد.",
                parse_mode="Markdown")
        except: pass
    # ۷. هشدار UN
    if nt % UN_INTERVAL == 5 and nt > 0:
        next_un = nt + 5
        for p in all_players():
            try:
                await ctx.bot.send_message(p["uid"],
                    f"🌍 *اطلاعیه*\n\n۵ نوبت دیگر (نوبت {next_un}) "
                    f"نشست عمومی سازمان ملل برگزار می‌شود.")
            except: pass
    # ۸. سازمان ملل
    if nt % UN_INTERVAL == 0 and nt > 0:
        try:
            if 'start_un' in globals():
                await start_un(ctx, nt)
        except Exception as e: log.warning(f"UN: {e}")
    # ۹. جاسوسی معلق
    try: await deliver_pending(ctx)
    except Exception as e: log.warning(f"deliver: {e}")
    # ۱۰. پایان سیزن
    if nt >= TOTAL_TURNS:
        gset("season_ended", "true")
        for p in players:
            try:
                await ctx.bot.send_message(p["uid"],
                    "🏁 *سیزن به پایان رسید!*\n\nبرای شروع جدید /start بزن.",
                    parse_mode="Markdown")
            except: pass

async def post_to_channel(ctx, text):
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"post_to_channel: {e}")# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — ادغام همه اخبار در یک فید
# ═══════════════════════════════════════════════════════════════

# ─── ارسال خبر به کانال — تابع مرکزی ───
async def news_post(ctx, title, body=""):
    """ارسال خبر به کانال با فرمت یکپارچه"""
    if body:
        text = f"📰 *{title}*\n━━━━━━━━━━━━━━━━\n{body}"
    else:
        text = f"📰 *{title}*"
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"news ch: {e}")

# ─── auto_turn جدید: فید ترکیبی ───
_old_auto_turn_news = auto_turn

async def auto_turn(ctx):
    if gget("season_ended") == "true": return
    # ۱. پیشرفت جنگ‌ها (بدون ارسال به کانال از این‌جا)
    advance_wars()
    # ۲. نوبت همه بازیکنان
    players = all_players()
    nt = int(gget("turn","1")) + 1
    gset("turn", nt)
    # جمع کردن همه‌ی خبرهای این نوبت
    news_items = []
    for p in players:
        try:
            res = process_turn(p["uid"])
            if not res: continue
            # رویداد تاریخی
            if res["ev"]:
                for e in res["ev"]:
                    news_items.append(("hist", e))
            # پیام شخصی به بازیکن
            t = f"📅 *نوبت {nt}* — {fmt_date(parse_date(res['date']))}\n"
            if res["ev"]:
                for e in res["ev"]:
                    t += f"• {e}\n"
            await ctx.bot.send_message(p["uid"], t,
                parse_mode="Markdown", reply_markup=kb_main())
        except Exception as e:
            log.warning(f"turn {p['uid']}: {e}")
    # ۳. چک کردن خبرهای عمومی جدید
    conn = db()
    public_cats = ("war","battle","conquest","protest","suppress",
                   "un","statement","item","holocaust","peace",
                   "conscription","bomb")
    rows = conn.execute(
        f"SELECT * FROM news WHERE turn>=? AND cat IN ({','.join('?'*len(public_cats))}) ORDER BY id",
        (nt-2, *public_cats)).fetchall()
    conn.close()
    for r in rows:
        if any(c == r["cat"] for _, c in news_items): continue
        news_items.append((r["cat"], r["text"]))
    # ۴. ارسال همه به کانال به عنوان یه پست
    if news_items:
        lines = [f"📰 *WORLD WAR NEWS — نوبت {nt}*",
                 f"🗓️ {fmt_date(parse_date(next_date(get_state(players[0]['uid'])['game_date'] if players else '1939-09-01')))}",
                 "━━━━━━━━━━━━━━━━"]
        cat_emoji = {
            "hist":"📜","war":"⚔️","battle":"🎯","conquest":"🏆",
            "protest":"🔥","suppress":"🚔","un":"🌍","statement":"📢",
            "item":"🎁","holocaust":"⚫","peace":"☮️",
            "conscription":"📋","bomb":"✈️",
        }
        for cat, txt in news_items:
            em = cat_emoji.get(cat, "•")
            lines.append(f"{em} {txt}")
        full = "\n".join(lines)
        try:
            await ctx.bot.send_message(NEWS_CH, full, parse_mode="Markdown")
        except Exception as e:
            log.warning(f"news post: {e}")
    # ۵. خبر سرگرمی هر ۵ نوبت
    if nt % 5 == 0:
        try:
            news = random.choice(RANDOM_NEWS)
            n = random.randint(10, 500)
            await ctx.bot.send_message(NEWS_CH,
                f"📰 *خبر سرگرمی*\n\n{news.format(n=n)}",
                parse_mode="Markdown")
        except: pass
    # ۶. اتم
    if nt == ATOMIC_UNLOCK:
        try:
            await ctx.bot.send_message(NEWS_CH,
                "☢️ *پروژه اتمی*\n\nپروژه منهتن امروز رسماً آغاز شد. "
                "آلمان و آمریکا وارد مرحله جدیدی از تحقیقات هسته‌ای شدند.",
                parse_mode="Markdown")
        except: pass
    # ۷. هشدار UN
    if nt % UN_INTERVAL == 5 and nt > 0:
        next_un = nt + 5
        for p in all_players():
            try:
                await ctx.bot.send_message(p["uid"],
                    f"🌍 *اطلاعیه*\n\n۵ نوبت دیگر (نوبت {next_un}) "
                    f"نشست عمومی سازمان ملل برگزار می‌شود.")
            except: pass
    # ۸. سازمان ملل
    if nt % UN_INTERVAL == 0 and nt > 0:
        try:
            # فقط اگه start_un جدید تعریف شده
            if 'start_un' in globals():
                await start_un(ctx, nt)
        except Exception as e: log.warning(f"UN: {e}")
    # ۹. جاسوسی معلق
    try: await deliver_pending(ctx)
    except Exception as e: log.warning(f"deliver: {e}")
    # ۱۰. پایان سیزن
    if nt >= TOTAL_TURNS:
        gset("season_ended", "true")
        for p in players:
            try:
                await ctx.bot.send_message(p["uid"],
                    "🏁 *سیزن به پایان رسید!*\n\nبرای شروع جدید /start بزن.",
                    parse_mode="Markdown")
            except: pass

# ─── post_to_channel ساده (بدون فیلتر اضافی) ───
async def post_to_channel(ctx, text):
    """ارسال فوری به کانال"""
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"post_to_channel: {e}")# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — حذف neglect، ۱ اقدام از هر بخش در نوبت
# ═══════════════════════════════════════════════════════════════

# دسته‌بندی اقدامات
ACTION_SECTION = {
    # امور مردم
    "🏥 بیمارستان جدید": "people",
    "📚 مدرسه جدید": "people",
    "💧 سیستم آب": "people",
    "🏠 مسکن عمومی": "people",
    "🍞 سهمیه غذا": "people",
    # امور حکومت
    "📜 اصلاحات مدنی": "gov",
    "⚖️ اصلاح قضایی": "gov",
    "💰 مبارزه با فساد": "gov",
    "🏛️ قانون اساسی": "gov",
    "📻 تبلیغات دولتی": "gov",
    # دولت
    "💼 برنامه اشتغال": "state",
    "🏗️ زیرساخت": "state",
    "🎓 دانشگاه ملی": "state",
    # مشکلات
    "🚨 مبارزه با جرم": "problems",
    # تورم
    "📉 کنترل قیمت‌ها": "inflation",
}

def can_do_action(uid, action):
    st = get_state(uid)
    if not st: return False, "❌ خطا"
    info = INTERNAL_ACTIONS.get(action)
    if not info: return False, "❌ اقدام نامعتبر"
    section = ACTION_SECTION.get(action, "misc")
    # سقف کل
    count = get_action_count(uid, action)
    if count >= info["max"]:
        return False, f"❌ این اقدام حداکثر {info['max']} بار قابل انجام است."
    # چک کن همین اقدام الان تو صف نباشه
    in_q = any(p["category"] == "internal_action" and p["model"] == action
               for p in get_pq(uid))
    if in_q:
        return False, "⏳ این اقدام در حال اجراست."
    # چک کن این نوبت تو این بخش اقدامی نکرده
    key = f"section_{section}_{uid}"
    last_section = int(gget(key, "0") or 0)
    if last_section == st["turn"]:
        return False, "⚠️ در این نوبت یک اقدام از این بخش انجام دادی. بخش دیگه‌ای یا نوبت بعد."
    # منابع
    if not is_admin(uid):
        if st["money"] < info["money"]:
            return False, f"❌ نیاز: {info['money']}💰 (داری {fmt(st['money'])})"
        if st["steel"] < info["steel"]:
            return False, f"❌ نیاز: {info['steel']}⚙️ (داری {fmt(st['steel'])})"
    return True, info

async def on_int_action(update, ctx, action):
    uid = update.effective_user.id
    ok, data = can_do_action(uid, action)
    if not ok:
        await update.message.reply_text(data)
        return
    info = data
    section = ACTION_SECTION.get(action, "misc")
    if not pay(uid, money=info["money"], steel=info["steel"]):
        await update.message.reply_text("❌ منابع کافی نیست.")
        return
    conn = db()
    conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
        (uid, "internal_action", action, 1, info["turns"]))
    conn.commit(); conn.close()
    gset(f"section_{section}_{uid}", str(get_state(uid)["turn"]))
    count = get_action_count(uid, action) + 1
    section_fa = {
        "people": "امور مردم", "gov": "امور حکومت",
        "state": "دولت", "problems": "مشکلات", "inflation": "تورم",
    }.get(section, "سایر")
    await update.message.reply_text(
        f"🏛️ *{action}*\n"
        f"📁 بخش: {section_fa}\n\n"
        f"🔨 در حال اجرا\n"
        f"⏱️ {info['turns']} نوبت دیگر\n"
        f"💰 {info['money']} | ⚙️ {info['steel']}\n"
        f"📊 رضایت پس از تکمیل: +{info['hap']}\n"
        f"🔢 اجرای {count} از {info['max']}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── حذف neglect از process_turn ───
_old_process_turn_neg = process_turn

def process_turn(uid):
    # چک نکن neglect رو
    return _old_process_turn_neg(uid)

# ─── hook روتر ───
_old_on_text_neg = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text_neg(update, ctx)
    text = update.message.text.strip()
    if text in INTERNAL_ACTIONS:
        await on_int_action(update, ctx, text); return
    return await _old_on_text_neg(update, ctx)

# ─── on_internal بدون هشدار neglect ───
async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    t = (f"🏛️ *امور کشور*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n")
    if st.get("protest"):
        t += f"🔥 اعتراض فعال ({st.get('protest_t',0)} نوبت)"
    t += ("\n\n💡 *در هر نوبت، از هر بخش یک اقدام می‌تونی بکنی*\n\n"
          "👇 بخش مورد نظر:")
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — فیکس زنجیره تحقیقات
# ═══════════════════════════════════════════════════════════════

# مدل اول (index 0) همیشه باز — چک زنجیره فقط از index 1
def research_chain_ok(uid, cat, idx, tree, researched):
    """اگه idx == 0 → همه چی اوکیه (مدل اول از اول بازه)"""
    if idx <= 0:
        return True, None
    # از index 1 چک کن تا idx-1
    for j in range(1, idx):
        if tree[j][0] not in researched:
            return False, tree[j][0]
    return True, None

async def on_research_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"research_{cat}"
    lines = [f"🔬 *{CAT_N[cat]}*","━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power, cost, build, steel, oil, desc = item
        if i == 0:
            lines.append(f"✅ *{name}* (از اول باز)")
            continue
        if name in researched:
            lines.append(f"✅ *{name}* — قدرت {power}")
            continue
        # چک زنجیره (فقط از index 1)
        ok, need = research_chain_ok(uid, cat, i, tree, researched)
        if not ok:
            lines.append(f"🔒 *{name}* (ابتدا {need} را تحقیق کن)")
        else:
            lines.append(
                f"🔓 *{name}*\n"
                f"   📝 {desc}\n"
                f"   💪 {power} | 🔬 {cost}💰+{build}نوبت | ⚙️{steel} 🛢️{oil}"
            )
    lines.append("\n👇 روی مدل بزن")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

# ─── hook روتر برای پیک تحقیقات ───
_old_on_text13 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text13(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    st = get_state(uid)
    if not st:
        return await _old_on_text13(update, ctx)
    screen = ctx.user_data.get("screen", "menu")
    if screen.startswith("research_"):
        cat = screen.split("_", 1)[1]
        tree = get_tree(st["country"], cat)
        researched = get_res(uid, cat)
        for i, item in enumerate(tree):
            if len(item) < 7: continue
            name, power, cost, build, steel, oil, desc = item
            if name == text:
                if i == 0:
                    await update.message.reply_text("این مدل از اول باز است.")
                    return
                if name in researched:
                    await update.message.reply_text("قبلاً تحقیق شده.")
                    return
                # چک زنجیره (فقط از index 1)
                ok, need = research_chain_ok(uid, cat, i, tree, researched)
                if not ok:
                    await update.message.reply_text(
                        f"🔒 ابتدا باید *{need}* را تحقیق کنی.",
                        parse_mode="Markdown")
                    return
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰")
                    return
                conn = db()
                conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
                    (uid, "research_pending", f"{cat}:{name}", 1, build))
                conn.commit(); conn.close()
                await update.message.reply_text(
                    f"🔬 *{name}* در صف تحقیق!\n⏱️ {build} نوبت\n💰 {cost}",
                    reply_markup=kb_main(), parse_mode="Markdown")
                return
    return await _old_on_text13(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — اقدامات امور کشور با محدودیت واقعی
# ═══════════════════════════════════════════════════════════════

# هر اقدام: money, steel, turns (زمان ساخت), hap (رضایت), max (سقف کل)
INTERNAL_ACTIONS = {
    # ─── یک‌بار برای همیشه ───
    "📜 اصلاحات مدنی": {"money": 5000, "steel": 500, "turns": 8, "hap": 5, "max": 1},
    "⚖️ اصلاح قضایی": {"money": 4000, "steel": 300, "turns": 6, "hap": 4, "max": 1},
    "💰 مبارزه با فساد": {"money": 6000, "steel": 200, "turns": 10, "hap": 6, "max": 1},
    "🏛️ قانون اساسی": {"money": 7000, "steel": 400, "turns": 12, "hap": 5, "max": 1},
    "🎓 دانشگاه ملی": {"money": 5000, "steel": 500, "turns": 8, "hap": 4, "max": 1},
    # ─── قابل تکرار با سقف ───
    "🏥 بیمارستان جدید": {"money": 2500, "steel": 250, "turns": 5, "hap": 2, "max": 10},
    "📚 مدرسه جدید": {"money": 1500, "steel": 150, "turns": 4, "hap": 2, "max": 15},
    "💧 سیستم آب": {"money": 3000, "steel": 300, "turns": 6, "hap": 3, "max": 5},
    "🏠 مسکن عمومی": {"money": 4000, "steel": 400, "turns": 7, "hap": 3, "max": 8},
    "🍞 سهمیه غذا": {"money": 1000, "steel": 0, "turns": 3, "hap": 1, "max": 30},
    "📻 تبلیغات دولتی": {"money": 800, "steel": 0, "turns": 2, "hap": 1, "max": 50},
    "🚨 مبارزه با جرم": {"money": 2000, "steel": 100, "turns": 4, "hap": 2, "max": 15},
    "💼 برنامه اشتغال": {"money": 3000, "steel": 200, "turns": 5, "hap": 3, "max": 10},
    "🏗️ زیرساخت": {"money": 3500, "steel": 400, "turns": 6, "hap": 3, "max": 8},
    "📉 کنترل قیمت‌ها": {"money": 2000, "steel": 0, "turns": 3, "hap": 2, "max": 20},
}

def get_action_count(uid, action):
    return int(gget(f"acount_{action.replace(' ','_')}_{uid}", "0") or 0)

def can_do_action(uid, action):
    st = get_state(uid)
    if not st: return False, "❌ خطا"
    info = INTERNAL_ACTIONS.get(action)
    if not info: return False, "❌ اقدام نامعتبر"
    # سقف
    count = get_action_count(uid, action)
    if count >= info["max"]:
        return False, f"❌ این اقدام حداکثر {info['max']} بار قابل انجام است."
    # چک کن همین اقدام الان تو صف نباشه
    in_q = any(p["category"] == "internal_action" and p["model"] == action
               for p in get_pq(uid))
    if in_q:
        return False, "⏳ این اقدام در حال اجراست."
    # یک اقدام در هر نوبت
    last_any = int(gget(f"last_action_any_{uid}", "0") or 0)
    if last_any == st["turn"]:
        return False, "⚠️ در این نوبت یک اقدام انجام دادی. نوبت بعد دوباره امتحان کن."
    # منابع
    if not is_admin(uid):
        if st["money"] < info["money"]:
            return False, f"❌ نیاز: {info['money']}💰 (داری {fmt(st['money'])})"
        if st["steel"] < info["steel"]:
            return False, f"❌ نیاز: {info['steel']}⚙️ (داری {fmt(st['steel'])})"
    return True, info

async def on_int_action(update, ctx, action):
    uid = update.effective_user.id
    ok, data = can_do_action(uid, action)
    if not ok:
        await update.message.reply_text(data)
        return
    info = data
    # پرداخت
    if not pay(uid, money=info["money"], steel=info["steel"]):
        await update.message.reply_text("❌ منابع کافی نیست.")
        return
    # ثبت تو صف
    conn = db()
    conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
        (uid, "internal_action", action, 1, info["turns"]))
    conn.commit(); conn.close()
    gset(f"last_action_any_{uid}", str(get_state(uid)["turn"]))
    gset(f"last_int_{uid}", str(get_state(uid)["turn"]))
    count = get_action_count(uid, action) + 1
    await update.message.reply_text(
        f"🏛️ *{action}*\n\n"
        f"🔨 در حال اجرا\n"
        f"⏱️ {info['turns']} نوبت دیگر\n"
        f"💰 {info['money']} | ⚙️ {info['steel']}\n"
        f"📊 رضایت پس از تکمیل: +{info['hap']}\n"
        f"🔢 اجرای {count} از {info['max']}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── پردازش اقدامات در process_turn ───
_old_pt12 = process_turn

def process_turn(uid):
    # قبل از اجرای قبلی، صف اقدامات داخلی
    st = get_state(uid)
    if st:
        conn = db()
        for item in conn.execute(
            "SELECT * FROM pq WHERE user_id=? AND category='internal_action'",
            (uid,)).fetchall():
            t = item["turns"] - 1
            if t <= 0:
                action = item["model"]
                info = INTERNAL_ACTIONS.get(action, {})
                hap_gain = info.get("hap", 1)
                st2 = get_state(uid)
                if st2:
                    sset(uid, happiness=min(100, st2["happiness"]+hap_gain))
                # ثبت تعداد
                count = get_action_count(uid, action) + 1
                gset(f"acount_{action.replace(' ','_')}_{uid}", str(count))
                conn.execute("DELETE FROM pq WHERE id=?", (item["id"],))
            else:
                conn.execute("UPDATE pq SET turns=? WHERE id=?", (t, item["id"]))
        conn.commit(); conn.close()
    # بعد process_turn اصلی
    return _old_pt12(uid)

# ─── hook روتر ───
_old_on_text12 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text12(update, ctx)
    text = update.message.text.strip()
    if text in INTERNAL_ACTIONS:
        await on_int_action(update, ctx, text); return
    return await _old_on_text12(update, ctx)

# ─── کیبورد امور مردم (بدون هزینه/رایگان) ───
async def on_people_affairs(update, ctx):
    uid = update.effective_user.id
    await update.message.reply_text(
        "👥 *امور مردم*\n\nچه خدمتی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🏥 بیمارستان جدید"),KeyboardButton("📚 مدرسه جدید")],
            [KeyboardButton("💧 سیستم آب"),KeyboardButton("🏠 مسکن عمومی")],
            [KeyboardButton("🍞 سهمیه غذا")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_gov_affairs(update, ctx):
    await update.message.reply_text(
        "🏛️ *امور حکومت*\n\nچه اصلاحی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📜 اصلاحات مدنی"),KeyboardButton("⚖️ اصلاح قضایی")],
            [KeyboardButton("💰 مبارزه با فساد"),KeyboardButton("🏛️ قانون اساسی")],
            [KeyboardButton("📻 تبلیغات دولتی")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_state_affairs(update, ctx):
    await update.message.reply_text(
        "🏢 *دولت*\n\nچه اقدامی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("💼 برنامه اشتغال"),KeyboardButton("🏗️ زیرساخت")],
            [KeyboardButton("🎓 دانشگاه ملی")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_problems(update, ctx):
    await update.message.reply_text(
        "📊 *مشکلات*\n\nکدوم؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🚨 مبارزه با جرم")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_inflation(update, ctx):
    await update.message.reply_text(
        "📈 *تورم*\n\nسیاست؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📉 کنترل قیمت‌ها")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — محدودیت اقدامات امور کشور
# ═══════════════════════════════════════════════════════════════

# هر اقدام: (هزینه، رضایت، کول‌داون نوبت، توضیح)
INTERNAL_ACTIONS = {
    "🏥 بیمارستان جدید": (500, 5, 3, "بیمارستان مدرن افتتاح شد."),
    "📚 مدرسه جدید": (400, 4, 3, "مدارس جدید ساخته شدند."),
    "💧 سیستم آب": (600, 6, 4, "آب سالم به همه رسید."),
    "🏠 مسکن": (700, 7, 4, "پروژه مسکن عمومی آغاز شد."),
    "🍞 سهمیه غذا": (400, 5, 2, "سهمیه غذایی توزیع شد."),
    "📜 اصلاحات مدنی": (600, 6, 5, "قوانین مدنی اصلاح شد."),
    "⚖️ قضایی": (500, 5, 5, "سیستم قضایی تقویت شد."),
    "💰 مبارزه با فساد": (800, 8, 6, "فساد اداری سرکوب شد."),
    "📻 تبلیغات": (500, 5, 3, "رسانه‌ها در خدمت دولت."),
    "💼 برنامه اشتغال": (900, 9, 5, "فرصت‌های شغلی جدید."),
    "🏗️ زیرساخت": (800, 7, 4, "پروژه‌های زیربنایی آغاز شد."),
    "🚨 مبارزه با جرم": (700, 6, 4, "نیروهای پلیس تقویت شدند."),
    "🏭 بیکاری": (900, 8, 5, "کارخانه‌های جدید افتتاح."),
    "🚧 اعتراضات": (500, 5, 3, "کانال‌های گفتگو با معترضان."),
    "💰 کاهش مالیات": (0, 3, 8, "مالیات کمی کاهش یافت."),
    "📉 کنترل قیمت‌ها": (600, 6, 5, "قیمت‌ها کنترل شد."),
}

def can_do_action(uid, action):
    """چک کن می‌تونه این اقدام رو بکنه؟"""
    st = get_state(uid)
    if not st: return False, "❌ خطا"
    info = INTERNAL_ACTIONS.get(action)
    if not info: return False, "❌ اقدام نامعتبر"
    cost, sat, cd, desc = info
    # کول‌داون
    key = f"action_{action.replace(' ','_')}_{uid}"
    last = int(gget(key, "0") or 0)
    if last > 0:
        turns_since = st["turn"] - last
        if turns_since < cd:
            rem = cd - turns_since
            return False, f"⏳ این اقدام {rem} نوبت دیگر قابل استفاده است."
    # اگه پرداخت نمی‌تونه
    if not is_admin(uid):
        if st["money"] < cost:
            return False, f"❌ نیاز: {cost}💰"
    # حد روزانه — حداکثر ۱ اقدام در هر نوبت
    last_any = int(gget(f"last_action_any_{uid}", "0") or 0)
    if last_any == st["turn"]:
        return False, "⚠️ در این نوبت یک اقدام انجام دادی. نوبت بعد دوباره."
    return True, (cost, sat, desc)

async def on_int_action(update, ctx, action):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    ok, data = can_do_action(uid, action)
    if not ok:
        await update.message.reply_text(data)
        return
    cost, sat, desc = data
    if cost > 0:
        if not pay(uid, money=cost):
            await update.message.reply_text(f"❌ نیاز: {cost}💰")
            return
    st2 = get_state(uid)
    sset(uid, happiness=min(100, st2["happiness"]+sat))
    gset(f"action_{action.replace(' ','_')}_{uid}", str(st["turn"]))
    gset(f"last_action_any_{uid}", str(st["turn"]))
    gset(f"last_int_{uid}", str(st["turn"]))
    cd = INTERNAL_ACTIONS[action][2]
    await update.message.reply_text(
        f"✅ *{action}*\n\n{desc}\n\n"
        f"😊 رضایت: +{sat}\n"
        f"💰 هزینه: {cost}\n"
        f"⏳ کول‌داون: {cd} نوبت",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── hook روتر ───
_old_on_text11 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text11(update, ctx)
    text = update.message.text.strip()
    if text in INTERNAL_ACTIONS:
        await on_int_action(update, ctx, text); return
    return await _old_on_text11(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ کامل — همه تغییرات جدید
# ═══════════════════════════════════════════════════════════════

# ─── ۱. کیبورد اصلی: حذف اقتصاد ───
def kb_main():
    return ReplyKeyboardMarkup([
        [KeyboardButton("⚔️ ارتش"),KeyboardButton("🔬 تحقیقات")],
        [KeyboardButton("🏭 کارخونه‌ها"),KeyboardButton("🤝 دیپلماسی")],
        [KeyboardButton("📦 تجارت"),KeyboardButton("🎯 حمله")],
        [KeyboardButton("🕵️ جاسوسی"),KeyboardButton("💵 مالیات")],
        [KeyboardButton("🏛️ امور کشور"),KeyboardButton("📊 آمار کامل")],
    ],resize_keyboard=True)

# ─── ۲. مالیات ۱-۱۰۰ ───
async def on_tax(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    ctx.user_data["wait"] = "tax"
    c = COUNTRIES[st["country"]]
    cur = int(c["bm"] * (st["tax"]/20))
    await update.message.reply_text(
        f"💵 *مالیات*\n\n"
        f"📊 فعلی: {st['tax']}%\n"
        f"📈 درآمد در نوبت: +{fmt(cur)}\n"
        f"😊 رضایت: {int(st['happiness'])}%\n\n"
        f"عددی از ۱ تا ۱۰۰ بفرست.\n"
        f"هرچه بیشتر → پول بیشتر، رضایت کمتر، خطر اعتراض بالاتر.",
        reply_markup=kb_back(), parse_mode="Markdown")

async def on_tax_input(update, ctx):
    if ctx.user_data.get("wait") != "tax": return False
    text = update.message.text.strip().replace("%","").strip()
    try:
        v = int(text)
        if not (1 <= v <= 100): raise ValueError
    except:
        await update.message.reply_text("❌ فرمت نامعتبر. عدد ۱ تا ۱۰۰ بفرست.")
        return True
    uid = update.effective_user.id
    st = get_state(uid)
    sset(uid, tax=v)
    c = COUNTRIES[st["country"]]
    new_income = int(c["bm"] * (v/20))
    ctx.user_data["wait"] = None
    st2 = get_state(uid)
    warn = ""
    if v >= 70:
        warn = "\n⚠️ مالیات بسیار بالا! خطر اعتراض جدی."
    elif v >= 50:
        warn = "\n⚠️ مالیات بالا — نارضایتی در راه."
    await update.message.reply_text(
        f"✅ مالیات: {v}%\n"
        f"📈 درآمد در نوبت: +{fmt(new_income)}{warn}\n\n"
        f"{render_dash(st2)}",
        reply_markup=kb_main(), parse_mode="Markdown")
    return True

# ─── ۳. تحقیقات: گیت زنجیره‌ای ───
def research_chain_ok(uid, cat, idx, tree, researched):
    """فقط اگه همه قبلی‌ها تحقیق شده باشن"""
    for j in range(idx):
        if tree[j][0] not in researched:
            return False, tree[j][0]
    return True, None

async def on_research_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"research_{cat}"
    lines = [f"🔬 *{CAT_N[cat]}*","━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power, cost, build, steel, oil, desc = item
        if i == 0 or name in researched:
            lines.append(f"✅ *{name}* — قدرت {power}")
        else:
            # چک کن قبلی‌ها تحقیق شدن
            ok, need = research_chain_ok(uid, cat, i, tree, researched)
            if not ok:
                lines.append(f"🔒 *{name}* (ابتدا {need} را تحقیق کن)")
            else:
                lines.append(
                    f"🔓 *{name}*\n"
                    f"   📝 {desc}\n"
                    f"   💪 {power} | 🔬 {cost}💰+{build}نوبت | ⚙️{steel} 🛢️{oil}"
                )
    lines.append("\n👇 روی مدل بزن")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

# ─── ۴. امور کشور گسترده ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب اعتراض")])
    rows.append([KeyboardButton("👥 امور مردم")])
    rows.append([KeyboardButton("🏛️ امور حکومت")])
    rows.append([KeyboardButton("🏢 دولت")])
    rows.append([KeyboardButton("📊 مشکلات")])
    rows.append([KeyboardButton("📈 تورم")])
    rows.append([KeyboardButton("🕵️ نظارت بر مردم")])
    if st and st["country"] == "germany" and st.get("gov") == "nazism":
        rows.append([KeyboardButton("⚫ هولوکاست")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    last = int(gget(f"last_int_{uid}", "0") or 0)
    turns_since = st["turn"] - last if last else 0
    t = (f"🏛️ *امور کشور*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n")
    if st.get("protest"):
        t += f"🔥 اعتراض فعال ({st.get('protest_t',0)} نوبت)"
    if turns_since >= 15:
        t += f"\n\n⚠️ *{turns_since} نوبت بی‌اقدام* — رضایت افتاده"
    t += "\n\n👇 بخش مورد نظر:"
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")

async def on_int_action(update, ctx, cost, sat_gain, title, desc):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    if not pay(uid, money=cost):
        await update.message.reply_text(f"❌ نیاز: {cost}💰")
        return
    sset(uid, happiness=min(100, st["happiness"]+sat_gain))
    gset(f"last_int_{uid}", str(st["turn"]))
    await update.message.reply_text(
        f"{title}\n\n{desc}\n\n😊 رضایت: +{sat_gain}",
        reply_markup=kb_main())

async def on_people_affairs(update, ctx):
    uid = update.effective_user.id
    await update.message.reply_text(
        "👥 *امور مردم*\n\nچه خدمتی به مردم می‌دی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🏥 بیمارستان جدید"),KeyboardButton("📚 مدرسه جدید")],
            [KeyboardButton("💧 سیستم آب"),KeyboardButton("🏠 مسکن")],
            [KeyboardButton("🍞 سهمیه غذا")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_gov_affairs(update, ctx):
    await update.message.reply_text(
        "🏛️ *امور حکومت*\n\nچه اصلاحی انجام می‌دی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📜 اصلاحات مدنی"),KeyboardButton("⚖️ قضایی")],
            [KeyboardButton("💰 مبارزه با فساد"),KeyboardButton("📻 تبلیغات")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_state_affairs(update, ctx):
    await update.message.reply_text(
        "🏢 *دولت*\n\nچه کاری برای دستگاه دولتی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("💼 برنامه اشتغال"),KeyboardButton("🏗️ زیرساخت")],
            [KeyboardButton("📋 خدمت اجباری")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_problems(update, ctx):
    await update.message.reply_text(
        "📊 *مشکلات*\n\nکدوم مشکل رو حل کنی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🚨 مبارزه با جرم"),KeyboardButton("🏭 بیکاری")],
            [KeyboardButton("🚧 اعتراضات")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_inflation(update, ctx):
    await update.message.reply_text(
        "📈 *تورم*\n\nسیاست اقتصادی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("💰 کاهش مالیات"),KeyboardButton("📉 کنترل قیمت‌ها")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

# ─── ۵. بمب تزار = فتح کامل ───
async def apply_item_effect(ctx, uid, item_key, target_uid=None):
    st = get_state(uid)
    if not st: return "❌ خطا"
    c = COUNTRIES[st["country"]]
    result = "✅"
    # آیتم‌های بدون هدف
    if item_key in ("carpet_bomb", "war_speech", "war_storm", "revive",
                    "god_shield", "invisible", "double_attack", "lock_on",
                    "revenge", "seize_power"):
        if item_key == "carpet_bomb":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], happiness=max(0, ps["happiness"]-10))
            result = "🔥 بمباران قالی"
        elif item_key == "war_speech":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], money=max(0, ps["money"]*0.5))
            result = "📢 نطق جنگی"
        elif item_key == "war_storm":
            conn = db()
            conn.execute("DELETE FROM wars WHERE def_uid=?", (uid,))
            conn.commit(); conn.close()
            sset(uid, war=0)
            result = "🌪 طوفان جنگی"
        elif item_key == "revive":
            add_effect(uid, "revive", 999); result = "🔄 برگشت فوری"
        elif item_key == "god_shield":
            add_effect(uid, "shield", 60); result = "🛡 سپر جان"
        elif item_key == "invisible":
            add_effect(uid, "invisible", 30); result = "👻 نامرئی"
        elif item_key == "double_attack":
            add_effect(uid, "double_attack", 10); result = "⚡ دوبرابر حمله"
        elif item_key == "lock_on":
            add_effect(uid, "lock_on", 10); result = "🎯 قفل"
        elif item_key == "revenge":
            add_effect(uid, "revenge", 999); result = "💀 انتقام"
        elif item_key == "seize_power":
            add_effect(uid, "commander", 10); result = "👑 غصب قدرت"
        add_news(st["turn"], "item", result)
        return result
    # بمب تزار = فتح کامل
    if item_key == "tsar_bomb" and target_uid:
        ts = get_state(target_uid)
        if ts:
            # انتقال ۵۰٪ (چون بمب زدیم)
            sset(uid,
                 money=st["money"] + int(ts["money"]*0.5),
                 steel=st["steel"] + int(ts["steel"]*0.5),
                 oil=st["oil"] + int(ts["oil"]*0.5),
                 food=st["food"] + int(ts["food"]*0.5),
                 coal=st["coal"] + int(ts["coal"]*0.5),
                 water=st["water"] + int(ts["water"]*0.5),
                 manpower=st["manpower"] + int(ts["manpower"]*0.5),
                 soldiers=st["soldiers"] + int(ts["soldiers"]*0.5),
                 happiness=int((st["happiness"]+ts["happiness"])/2))
            # انتقال تحقیقات
            conn = db()
            rows = conn.execute("SELECT category,model FROM research WHERE user_id=?", (target_uid,)).fetchall()
            for r in rows:
                conn.execute("INSERT OR IGNORE INTO research(user_id,category,model) VALUES(?,?,?)",
                    (uid, r["category"], r["model"]))
            conn.commit(); conn.close()
            # کشتن
            sset(target_uid, dead=1)
            msg = (f"💣 *بمب تزار*\n\n"
                   f"بمب تزار توسط {c['n']} بر فراز پایتخت "
                   f"{COUNTRIES[ts['country']]['n']} منفجر شد. شهر کاملاً "
                   f"نابود شد و کشور فتح گردید.\n\n"
                   f"📊 {c['n']} ۵۰٪ دارایی‌ها + تحقیقات را به دست آورد.")
            add_news(st["turn"], "conquest", msg)
            try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
            except: pass
            result = f"💣 بمب تزار — {COUNTRIES[ts['country']]['n']} فتح شد."
    elif item_key == "force_exile" and target_uid:
        ts = get_state(target_uid)
        if ts: sset(target_uid, dead=1); result = "🗳 اخراج اجباری"
    elif item_key == "censor" and target_uid:
        add_effect(target_uid, "censored", 3); result = "🤐 سانسور"
    elif item_key == "expose" and target_uid:
        result = f"🕵️ افشاگری: {render_stats(target_uid)}"
    elif item_key == "force_ally" and target_uid:
        aid = get_user_alliance(uid)
        if not aid:
            conn = db()
            cur = conn.execute("INSERT INTO alliances(name,founder) VALUES(?,?)", (f"اتحاد {c['n']}", uid))
            aid = cur.lastrowid
            conn.execute("INSERT INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
            conn.commit(); conn.close()
        conn = db()
        conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, target_uid))
        conn.commit(); conn.close()
        result = "🤝 اتحاد اجباری"
    elif item_key == "plunder" and target_uid:
        ts = get_state(target_uid)
        if ts:
            half = ts["money"]//2
            sset(target_uid, money=ts["money"]-half)
            sset(uid, money=st["money"]+half)
            result = f"💰 غارت {fmt(half)}"
    elif item_key == "nuke_item" and target_uid:
        result = use_atomic(uid, target_uid)
    elif item_key == "bio_weapon" and target_uid:
        add_effect(target_uid, "no_attack", 5)
        result = "☠️ بیولوژیک"
    elif item_key == "ballistic" and target_uid:
        ts = get_state(target_uid)
        if ts: sset(target_uid, dead=1); result = "🚀 بالستیک"
    add_news(st["turn"], "item", result)
    return result

# ─── ۶. فیلتر کانال: هیچ اطلاعات شخصی ───
async def post_to_channel(ctx, text):
    """فقط اخبار عمومی و بدون اطلاعات شخصی"""
    # لیست کلمات ممنوعه
    forbidden = ["پول تو", "سرباز تو", "ارتش تو", "منابعت", "جاسوس تو"]
    for w in forbidden:
        if w in text:
            return
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"news: {e}")

# ─── ۷. hook روتر ───
_old_on_text7 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text7(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    # کیبورد اصلی جدید
    if text == "💵 مالیات":
        await on_tax(update, ctx); return
    # اقتصاد حذف شد
    if text == "💰 اقتصاد":
        await update.message.reply_text("ℹ️ این بخش حذف شد. از 💵 مالیات استفاده کن.")
        return
    # امور کشور
    if text == "🏛️ امور کشور":
        await on_internal(update, ctx); return
    if text == "👥 امور مردم":
        await on_people_affairs(update, ctx); return
    if text == "🏛️ امور حکومت":
        await on_gov_affairs(update, ctx); return
    if text == "🏢 دولت":
        await on_state_affairs(update, ctx); return
    if text == "📊 مشکلات":
        await on_problems(update, ctx); return
    if text == "📈 تورم":
        await on_inflation(update, ctx); return
    # اقدامات
    acts = {
        "🏥 بیمارستان جدید": (500, 5, "🏥 بیمارستان جدید", "بیمارستان مدرن افتتاح شد."),
        "📚 مدرسه جدید": (400, 4, "📚 مدرسه جدید", "مدارس جدید ساخته شدند."),
        "💧 سیستم آب": (600, 6, "💧 سیستم آب", "آب سالم به همه رسید."),
        "🏠 مسکن": (700, 7, "🏠 مسکن", "پروژه مسکن عمومی آغاز شد."),
        "🍞 سهمیه غذا": (400, 5, "🍞 سهمیه غذا", "سهمیه غذایی توزیع شد."),
        "📜 اصلاحات مدنی": (600, 6, "📜 اصلاحات مدنی", "قوانین مدنی اصلاح شد."),
        "⚖️ قضایی": (500, 5, "⚖️ قضایی", "سیستم قضایی تقویت شد."),
        "💰 مبارزه با فساد": (800, 8, "💰 مبارزه با فساد", "فساد اداری سرکوب شد."),
        "📻 تبلیغات": (500, 5, "📻 تبلیغات", "رسانه‌ها در خدمت دولت."),
        "💼 برنامه اشتغال": (900, 9, "💼 برنامه اشتغال", "فرصت‌های شغلی جدید."),
        "🏗️ زیرساخت": (800, 7, "🏗️ زیرساخت", "پروژه‌های زیربنایی آغاز شد."),
        "🚨 مبارزه با جرم": (700, 6, "🚨 مبارزه با جرم", "نیروهای پلیس تقویت شدند."),
        "🏭 بیکاری": (900, 8, "🏭 بیکاری", "کارخانه‌های جدید افتتاح."),
        "🚧 اعتراضات": (500, 5, "🚧 اعتراضات", "کانال‌های گفتگو با معترضان."),
        "💰 کاهش مالیات": (0, 3, "💰 کاهش مالیات", "مالیات کمی کاهش یافت."),
        "📉 کنترل قیمت‌ها": (600, 6, "📉 کنترل قیمت‌ها", "قیمت‌ها کنترل شد."),
    }
    if text in acts:
        cost, sat, title, desc = acts[text]
        await on_int_action(update, ctx, cost, sat, title, desc)
        return
    return await _old_on_text7(update, ctx)

# ─── ۸. neglect در نوبت ───
_old_pt8 = process_turn

def process_turn(uid):
    res = _old_pt8(uid)
    if not res: return res
    st = get_state(uid)
    if not st: return res
    last = int(gget(f"last_int_{uid}", "0") or 0)
    if last == 0:
        gset(f"last_int_{uid}", str(st["turn"]))
    elif st["turn"] - last >= 15:
        sset(uid, happiness=max(0, st["happiness"]-3))
    return res

# ─── ۹. مقدار مالیات تو process_turn (۱-۱۰۰) ───
_old_calc_hap9 = calc_hap_delta

def calc_hap_delta(uid, st):
    d = 0
    tax = st.get("tax", 20)
    # مالیات ۱-۱۰۰
    if tax >= 80: d -= 15
    elif tax >= 60: d -= 10
    elif tax >= 40: d -= 5
    elif tax >= 25: d -= 2
    elif tax <= 10: d += 3
    f = st.get("food", 0)
    if f < 100: d -= 5
    elif f < 300: d -= 2
    elif f > 3000: d += 2
    w = st.get("water", 0)
    if w < 50: d -= 4
    if st.get("steel", 0) < 50: d -= 2
    if st.get("oil", 0) <= 0: d -= 3
    if st.get("coal", 0) < 50: d -= 2
    if st.get("war"): d -= 3
    if st.get("protest"): d -= 4
    if st.get("suppress_cd", 0) > 0: d -= 2
    d -= st.get("surveillance", 20) // 15
    d += GOVS.get(st.get("gov"), ("",0))[1]
    facs = len(get_fact(uid))
    if facs < 3: d -= 2
    elif facs > 6: d += 1
    for pk in get_done_proj(uid):
        p = PROJECTS.get(pk, {})
        if p.get("eff") == "happiness": d += p.get("v",0)//3
    if "conscription" in get_done_proj(uid): d -= 3
    if st.get("money", 0) <= 100: d -= 3
    if is_vip(uid) and d < 0: d = int(d/2)
    return d

# ─── ۱۰. چک زنجیره تحقیق ───
_old_on_text10 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text10(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    st = get_state(uid)
    if not st:
        return await _old_on_text10(update, ctx)
    screen = ctx.user_data.get("screen", "menu")
    # تحقیق زنجیره‌ای
    if screen.startswith("research_"):
        cat = screen.split("_", 1)[1]
        tree = get_tree(st["country"], cat)
        researched = get_res(uid, cat)
        for i, item in enumerate(tree):
            if len(item) < 7: continue
            name, power, cost, build, steel, oil, desc = item
            if name == text:
                if i == 0:
                    await update.message.reply_text("این مدل از اول باز است.")
                    return
                if name in researched:
                    await update.message.reply_text("قبلاً تحقیق شده.")
                    return
                # چک زنجیره
                ok, need = research_chain_ok(uid, cat, i, tree, researched)
                if not ok:
                    await update.message.reply_text(
                        f"🔒 ابتدا باید *{need}* را تحقیق کنی.",
                        parse_mode="Markdown")
                    return
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰")
                    return
                conn = db()
                conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
                    (uid, "research_pending", f"{cat}:{name}", 1, build))
                conn.commit(); conn.close()
                await update.message.reply_text(
                    f"🔬 *{name}* در صف تحقیق!\n⏱️ {build} نوبت\n💰 {cost}",
                    reply_markup=kb_main(), parse_mode="Markdown")
                return
    return await _old_on_text10(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — هولوکاست + نازیسم
# ═══════════════════════════════════════════════════════════════

# ─── نام داینامیک کشور ───
def country_name(uid):
    st = get_state(uid)
    if not st: return "?"
    c = COUNTRIES[st["country"]]
    if st["country"] == "germany" and st.get("gov") == "nazism":
        return "آلمان نازی"
    return c["n"]

# ─── کیبورد حکومت با نازیسم ───
def kb_gov():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👑 پادشاهی مطلقه"),KeyboardButton("👑 پادشاهی مشروطه")],
        [KeyboardButton("🗳️ جمهوری ریاستی"),KeyboardButton("🗳️ جمهوری پارلمانی")],
        [KeyboardButton("🚩 فاشیسم"),KeyboardButton("⚫ نازیسم")],
        [KeyboardButton("🚩 کمونیسم"),KeyboardButton("🚩 تک‌حزبی")],
        [KeyboardButton("⚙️ دیکتاتوری نظامی"),KeyboardButton("⚙️ دیکتاتوری شخصی")],
        [KeyboardButton("🕊️ دموکراسی لیبرال"),KeyboardButton("🕊️ دموکراسی اجتماعی")],
        [KeyboardButton("⚖️ تئوکراسی")]],
        resize_keyboard=True, one_time_keyboard=True)

async def on_gov_pick(update, ctx):
    if ctx.user_data.get("wait") != "gov": return
    text = update.message.text.strip()
    gmap = {
        "👑 پادشاهی مطلقه":"absolute_monarchy",
        "👑 پادشاهی مشروطه":"constitutional_monarchy",
        "🗳️ جمهوری ریاستی":"presidential_republic",
        "🗳️ جمهوری پارلمانی":"parliamentary_republic",
        "🚩 فاشیسم":"fascist",
        "⚫ نازیسم":"nazism",
        "🚩 کمونیسم":"communism",
        "🚩 تک‌حزبی":"single_party",
        "⚙️ دیکتاتوری نظامی":"military_dictatorship",
        "⚙️ دیکتاتوری شخصی":"personal_dictatorship",
        "🕊️ دموکراسی لیبرال":"liberal_democracy",
        "🕊️ دموکراسی اجتماعی":"social_democracy",
        "⚖️ تئوکراسی":"theocracy",
    }
    if text not in gmap: return
    uid = update.effective_user.id
    pset(uid, gov=gmap[text])
    ctx.user_data["wait"] = None
    st = get_state(uid)
    await update.message.reply_text(f"✅\n\n{render_dash(st)}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── render_dash با نام داینامیک ───
def render_dash(st):
    c = COUNTRIES[st["country"]]
    name = "آلمان نازی" if (st["country"] == "germany" and
                              st.get("gov") == "nazism") else c["n"]
    return (f"{c['f']} *{name}* — {fmt_date(parse_date(st['game_date']))}\n"
            f"🔢 نوبت: {st['turn']} / {TOTAL_TURNS}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 {fmt(st['money'])}  🍞 {fmt(st['food'])}  ⚙️ {fmt(st['steel'])}\n"
            f"🛢️ {fmt(st['oil'])}  🪨 {fmt(st['coal'])}  👥 {fmt(st['manpower'])}\n"
            f"🪖 سرباز: {fmt(st['soldiers'])}\n"
            f"😊 {int(st['happiness'])}%  💵 {st['tax']}%")

# ─── render_stats با نام داینامیک ───
def render_stats(uid):
    st = get_state(uid); c = COUNTRIES[st["country"]]
    name = "آلمان نازی" if (st["country"] == "germany" and
                              st.get("gov") == "nazism") else c["n"]
    lines = [
        f"{c['f']} *{name}* — {fmt_date(parse_date(st['game_date']))}",
        f"🔢 نوبت {st['turn']}/{TOTAL_TURNS}",
        f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}",
        f"🆔 `{uid}`",
        "━━━━━━━━━━━━━━━━",
        f"💰{fmt(st['money'])} 🍞{fmt(st['food'])} 💧{fmt(st['water'])}",
        f"⚙️{fmt(st['steel'])} 🛢️{fmt(st['oil'])} 🪨{fmt(st['coal'])}",
        f"👥{fmt(st['manpower'])} 🪖{fmt(st['soldiers'])}",
        f"😊{int(st['happiness'])}% 💵{st['tax']}% 🕵️{st.get('surveillance',20)}%",
    ]
    for u in get_army(uid):
        lines.append(f"▪️ {u['model']}: {fmt(u['count'])}")
    aid = get_user_alliance(uid)
    if aid:
        members = [m for m in get_alliance_members(aid) if m != uid]
        names = []
        for m in members:
            ms = get_state(m)
            if ms: names.append(country_name(m))
        if names:
            lines.append(f"🤝 متحدین: {', '.join(names)}")
    conn = db()
    naps = conn.execute("SELECT * FROM nap WHERE a=? OR b=?", (uid, uid)).fetchall()
    conn.close()
    for n in naps:
        other = n["b"] if n["a"] == uid else n["a"]
        lines.append(f"🤐 NAP با {country_name(other)} تا نوبت {n['until_turn']}")
    conn = db()
    wars = conn.execute("SELECT * FROM wars WHERE atk_uid=? OR def_uid=?", (uid, uid)).fetchall()
    conn.close()
    for w in wars:
        if w["atk_uid"] == uid:
            lines.append(f"⚔️ حمله به {country_name(w['def_uid'])}")
        else:
            lines.append(f"🛡 دفاع از حمله {country_name(w['atk_uid'])}")
    return "\n".join(lines)

# ─── کیبورد امور کشور ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب اعتراض")])
    rows.append([KeyboardButton("🕵️ نظارت بر مردم")])
    if st and st["country"] == "germany" and st.get("gov") == "nazism":
        rows.append([KeyboardButton("⚫ هولوکاست")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    t = (f"🏛️ *امور کشور {country_name(uid)}*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n"
         f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}\n")
    if st.get("protest"):
        t += f"\n🔥 *اعتراض فعال* ({st.get('protest_t',0)} نوبت مانده)"
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")

# ─── هولوکاست ───
async def on_holocaust(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["country"] != "germany" or st.get("gov") != "nazism":
        await update.message.reply_text("❌ در دسترس نیست.")
        return
    if not pay(uid, money=3000):
        await update.message.reply_text("❌ ۳۰۰۰💰 لازمه.")
        return
    sset(uid,
         money=st["money"]+5000,
         steel=st["steel"]+200,
         happiness=max(0, st["happiness"]-20),
         manpower=int(st["manpower"]*0.9))
    add_effect(uid, "holocaust", 5)
    msg = (f"⚫ *هولوکاست*\n\n"
           f"رژیم نازی برنامه‌ای گسترده علیه یهودیان، کولی‌ها، معلولان و "
           f"بیماران روانی آغاز کرد. میلیون‌ها انسان به اردوگاه‌های کار "
           f"اجباری و اتاق‌های گاز فرستاده شدند.\n\n"
           f"📈 اقتصاد: +۵۰۰۰💰\n"
           f"📈 فولاد: +۲۰۰⚙️\n"
           f"📉 رضایت: -۲۰")
    add_news(st["turn"], "holocaust", msg)
    try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
    except: pass
    await update.message.reply_text(msg, reply_markup=kb_main(), parse_mode="Markdown")

# ─── hook روتر ───
_old_on_text6 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text6(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "⚫ هولوکاست":
        await on_holocaust(update, ctx); return
    if text == "🏛️ امور کشور":
        await on_internal(update, ctx); return
    return await _old_on_text6(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ ۶ — نازیسم + نام داینامیک
# ═══════════════════════════════════════════════════════════════

# ─── کیبورد حکومت با نازیسم ───
def kb_gov():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👑 پادشاهی مطلقه"),KeyboardButton("👑 پادشاهی مشروطه")],
        [KeyboardButton("🗳️ جمهوری ریاستی"),KeyboardButton("🗳️ جمهوری پارلمانی")],
        [KeyboardButton("🚩 فاشیسم"),KeyboardButton("⚫ نازیسم")],
        [KeyboardButton("🚩 کمونیسم"),KeyboardButton("🚩 تک‌حزبی")],
        [KeyboardButton("⚙️ دیکتاتوری نظامی"),KeyboardButton("⚙️ دیکتاتوری شخصی")],
        [KeyboardButton("🕊️ دموکراسی لیبرال"),KeyboardButton("🕊️ دموکراسی اجتماعی")],
        [KeyboardButton("⚖️ تئوکراسی")]],
        resize_keyboard=True, one_time_keyboard=True)

async def on_gov_pick(update, ctx):
    if ctx.user_data.get("wait") != "gov": return
    text = update.message.text.strip()
    gmap = {
        "👑 پادشاهی مطلقه":"absolute_monarchy",
        "👑 پادشاهی مشروطه":"constitutional_monarchy",
        "🗳️ جمهوری ریاستی":"presidential_republic",
        "🗳️ جمهوری پارلمانی":"parliamentary_republic",
        "🚩 فاشیسم":"fascist",
        "⚫ نازیسم":"nazism",
        "🚩 کمونیسم":"communism",
        "🚩 تک‌حزبی":"single_party",
        "⚙️ دیکتاتوری نظامی":"military_dictatorship",
        "⚙️ دیکتاتوری شخصی":"personal_dictatorship",
        "🕊️ دموکراسی لیبرال":"liberal_democracy",
        "🕊️ دموکراسی اجتماعی":"social_democracy",
        "⚖️ تئوکراسی":"theocracy",
    }
    if text not in gmap: return
    uid = update.effective_user.id
    pset(uid, gov=gmap[text])
    ctx.user_data["wait"] = None
    st = get_state(uid)
    await update.message.reply_text(f"✅\n\n{render_dash(st)}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── نام داینامیک کشور ───
def country_name(uid):
    """نام کشور با در نظر گرفتن حکومت"""
    st = get_state(uid)
    if not st: return "?"
    c = COUNTRIES[st["country"]]
    if st["country"] == "germany" and st.get("gov") == "nazism":
        return "آلمان نازی"
    return c["n"]

def country_flag(uid):
    st = get_state(uid)
    if not st: return "❓"
    return COUNTRIES[st["country"]]["f"]

# ─── render_dash با نام داینامیک ───
def render_dash(st):
    c = COUNTRIES[st["country"]]
    name = "آلمان نازی" if (st["country"] == "germany" and
                              st.get("gov") == "nazism") else c["n"]
    return (f"{c['f']} *{name}* — {fmt_date(parse_date(st['game_date']))}\n"
            f"🔢 نوبت: {st['turn']} / {TOTAL_TURNS}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 {fmt(st['money'])}  🍞 {fmt(st['food'])}  ⚙️ {fmt(st['steel'])}\n"
            f"🛢️ {fmt(st['oil'])}  🪨 {fmt(st['coal'])}  👥 {fmt(st['manpower'])}\n"
            f"🪖 سرباز: {fmt(st['soldiers'])}\n"
            f"😊 {int(st['happiness'])}%  💵 {st['tax']}%")

# ─── render_stats با نام داینامیک ───
def render_stats(uid):
    st = get_state(uid); c = COUNTRIES[st["country"]]
    name = "آلمان نازی" if (st["country"] == "germany" and
                              st.get("gov") == "nazism") else c["n"]
    lines = [
        f"{c['f']} *{name}* — {fmt_date(parse_date(st['game_date']))}",
        f"🔢 نوبت {st['turn']}/{TOTAL_TURNS}",
        f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}",
        f"🆔 `{uid}`",
        "━━━━━━━━━━━━━━━━",
        f"💰{fmt(st['money'])} 🍞{fmt(st['food'])} 💧{fmt(st['water'])}",
        f"⚙️{fmt(st['steel'])} 🛢️{fmt(st['oil'])} 🪨{fmt(st['coal'])}",
        f"👥{fmt(st['manpower'])} 🪖{fmt(st['soldiers'])}",
        f"😊{int(st['happiness'])}% 💵{st['tax']}% 🕵️{st.get('surveillance',20)}%",
    ]
    units = get_army(uid)
    if units:
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append("⚔️ *نیروهای مسلح:*")
        for u in units:
            lines.append(f"▪️ {u['model']}: {fmt(u['count'])}")
    aid = get_user_alliance(uid)
    if aid:
        members = [m for m in get_alliance_members(aid) if m != uid]
        if members:
            names = []
            for m in members:
                ms = get_state(m)
                if ms: names.append(country_name(m))
            lines.append(f"🤝 متحدین: {', '.join(names)}")
    conn = db()
    naps = conn.execute("SELECT * FROM nap WHERE a=? OR b=?", (uid, uid)).fetchall()
    conn.close()
    if naps:
        lines.append("━━━━━━━━━━━━━━━━")
        for n in naps:
            other = n["b"] if n["a"] == uid else n["a"]
            os_ = get_state(other)
            if os_:
                lines.append(f"🤐 پیمان عدم تعرض با {country_name(other)} (تا نوبت {n['until_turn']})")
    conn = db()
    wars = conn.execute("SELECT * FROM wars WHERE atk_uid=? OR def_uid=?", (uid, uid)).fetchall()
    conn.close()
    if wars:
        lines.append("━━━━━━━━━━━━━━━━")
        for w in wars:
            if w["atk_uid"] == uid:
                os_ = get_state(w["def_uid"])
                if os_: lines.append(f"⚔️ در حال حمله به {country_name(w['def_uid'])}")
            else:
                os_ = get_state(w["atk_uid"])
                if os_: lines.append(f"🛡 در حال دفاع از حمله {country_name(w['atk_uid'])}")
    effects = []
    for eff, name in [("shield","🛡 سپر جان"),("invisible","👻 نامرئی"),
                      ("double_attack","⚡ دوبرابر حمله"),("lock_on","🎯 قفل"),
                      ("commander","👑 فرمانده"),
                      ("censored","🤐 سانسور"),("no_attack","⛔ تحریم حمله")]:
        if has_effect(uid, eff): effects.append(name)
    if effects:
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append(f"✨ افکت‌های فعال: {', '.join(effects)}")
    return "\n".join(lines)

# ─── کیبورد امور کشور بدون ذکر نام ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب# ═══════════════════════════════════════════════════════════════
#  🩹 پچ ۵ — فیکس‌های نهایی
# ═══════════════════════════════════════════════════════════════

# ─── ۱. حذف کارخونه نظامی از پروژه‌ها ───
for _k in ["ammo_factory", "tank_factory", "fighter_factory",
           "jet_factory", "shipyard", "equip_factory", "chem_factory"]:
    if _k in PROJECTS:
        del PROJECTS[_k]

# ─── ۲. کیبورد مالیات جدید — مالیات واقعاً پول می‌ده ───
async def on_tax(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    ctx.user_data["wait"] = "tax"
    c = COUNTRIES[st["country"]]
    cur = int(c["bm"] * (st["tax"]/20))
    await update.message.reply_text(
        f"💵 *مالیات*\n\n"
        f"📊 مالیات فعلی: {st['tax']}%\n"
        f"📈 تولید فعلی: +{fmt(cur)} در نوبت\n\n"
        f"عدد بین ۰ تا ۵۰ بفرست.\n"
        f"هرچه بیشتر، درآمد بیشتر ولی رضایت کمتر.",
        reply_markup=kb_back(), parse_mode="Markdown")

async def on_tax_input(update, ctx):
    if ctx.user_data.get("wait") != "tax": return False
    text = update.message.text.strip().replace("%","").strip()
    try:
        v = int(text)
        if not (0 <= v <= 50): raise ValueError
    except:
        await update.message.reply_text("❌ فرمت نامعتبر. عدد ۰ تا ۵۰ بفرست.")
        return True
    uid = update.effective_user.id
    st = get_state(uid)
    sset(uid, tax=v)
    c = COUNTRIES[st["country"]]
    new_income = int(c["bm"] * (v/20))
    ctx.user_data["wait"] = None
    st2 = get_state(uid)
    await update.message.reply_text(
        f"✅ مالیات: {v}%\n"
        f"📈 درآمد هر نوبت: +{fmt(new_income)}\n\n"
        f"{render_dash(st2)}",
        reply_markup=kb_main(), parse_mode="Markdown")
    return True

# ─── ۳. کیبورد حکومت — «آلمان» به جای «نازیسم» ───
def kb_gov():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👑 پادشاهی مطلقه"),KeyboardButton("👑 پادشاهی مشروطه")],
        [KeyboardButton("🗳️ جمهوری ریاستی"),KeyboardButton("🗳️ جمهوری پارلمانی")],
        [KeyboardButton("🚩 فاشیسم"),KeyboardButton("⚫ آلمان")],
        [KeyboardButton("🚩 کمونیسم"),KeyboardButton("🚩 تک‌حزبی")],
        [KeyboardButton("⚙️ دیکتاتوری نظامی"),KeyboardButton("⚙️ دیکتاتوری شخصی")],
        [KeyboardButton("🕊️ دموکراسی لیبرال"),KeyboardButton("🕊️ دموکراسی اجتماعی")],
        [KeyboardButton("⚖️ تئوکراسی")]],
        resize_keyboard=True, one_time_keyboard=True)

async def on_gov_pick(update, ctx):
    if ctx.user_data.get("wait") != "gov": return
    text = update.message.text.strip()
    gmap = {
        "👑 پادشاهی مطلقه":"absolute_monarchy",
        "👑 پادشاهی مشروطه":"constitutional_monarchy",
        "🗳️ جمهوری ریاستی":"presidential_republic",
        "🗳️ جمهوری پارلمانی":"parliamentary_republic",
        "🚩 فاشیسم":"fascist",
        "⚫ آلمان":"nazism",
        "🚩 کمونیسم":"communism",
        "🚩 تک‌حزبی":"single_party",
        "⚙️ دیکتاتوری نظامی":"military_dictatorship",
        "⚙️ دیکتاتوری شخصی":"personal_dictatorship",
        "🕊️ دموکراسی لیبرال":"liberal_democracy",
        "🕊️ دموکراسی اجتماعی":"social_democracy",
        "⚖️ تئوکراسی":"theocracy",
    }
    if text not in gmap: return
    uid = update.effective_user.id
    pset(uid, gov=gmap[text])
    ctx.user_data["wait"] = None
    st = get_state(uid)
    await update.message.reply_text(f"✅\n\n{render_dash(st)}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── ۴. آمار کامل با اتحاد + پیمان‌ها + جنگ‌ها ───
def render_stats(uid):
    st = get_state(uid); c = COUNTRIES[st["country"]]
    lines = [
        f"{c['f']} *{c['n']}* — {fmt_date(parse_date(st['game_date']))}",
        f"🔢 نوبت {st['turn']}/{TOTAL_TURNS}",
        f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}",
        f"🆔 `{uid}`",
        "━━━━━━━━━━━━━━━━",
        f"💰{fmt(st['money'])} 🍞{fmt(st['food'])} 💧{fmt(st['water'])}",
        f"⚙️{fmt(st['steel'])} 🛢️{fmt(st['oil'])} 🪨{fmt(st['coal'])}",
        f"👥{fmt(st['manpower'])} 🪖{fmt(st['soldiers'])}",
        f"😊{int(st['happiness'])}% 💵{st['tax']}% 🕵️{st.get('surveillance',20)}%",
    ]
    units = get_army(uid)
    if units:
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append("⚔️ *نیروهای مسلح:*")
        for u in units:
            lines.append(f"▪️ {u['model']}: {fmt(u['count'])}")
    aid = get_user_alliance(uid)
    if aid:
        members = [m for m in get_alliance_members(aid) if m != uid]
        if members:
            names = []
            for m in members:
                ms = get_state(m)
                if ms: names.append(COUNTRIES[ms["country"]]["n"])
            lines.append(f"🤝 متحدین: {', '.join(names)}")
    conn = db()
    naps = conn.execute("SELECT * FROM nap WHERE a=? OR b=?", (uid, uid)).fetchall()
    conn.close()
    if naps:
        lines.append("━━━━━━━━━━━━━━━━")
        for n in naps:
            other = n["b"] if n["a"] == uid else n["a"]
            os_ = get_state(other)
            if os_:
                lines.append(f"🤐 پیمان عدم تعرض با {COUNTRIES[os_['country']]['n']} (تا نوبت {n['until_turn']})")
    conn = db()
    wars = conn.execute("SELECT * FROM wars WHERE atk_uid=? OR def_uid=?", (uid, uid)).fetchall()
    conn.close()
    if wars:
        lines.append("━━━━━━━━━━━━━━━━")
        for w in wars:
            if w["atk_uid"] == uid:
                os_ = get_state(w["def_uid"])
                if os_: lines.append(f"⚔️ در حال حمله به {COUNTRIES[os_['country']]['n']}")
            else:
                os_ = get_state(w["atk_uid"])
                if os_: lines.append(f"🛡 در حال دفاع از حمله {COUNTRIES[os_['country']]['n']}")
    effects = []
    for eff, name in [("shield","🛡 سپر جان"),("invisible","👻 نامرئی"),
                      ("double_attack","⚡ دوبرابر حمله"),("lock_on","🎯 قفل"),
                      ("commander","👑 فرمانده"),("special","⚫ تصمیم ویژه"),
                      ("censored","🤐 سانسور"),("no_attack","⛔ تحریم حمله")]:
        if has_effect(uid, eff): effects.append(name)
    if effects:
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append(f"✨ افکت‌های فعال: {', '.join(effects)}")
    return "\n".join(lines)

# ─── ۵. امور کشور گسترده با اقدامات داخلی ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب اعتراض")])
    rows.append([KeyboardButton("🕵️ نظارت بر مردم")])
    rows.append([KeyboardButton("📢 تبلیغات دولتی"), KeyboardButton("🏥 خدمات درمانی")])
    rows.append([KeyboardButton("📚 آموزش عمومی"), KeyboardButton("💰 یارانه")])
    if st and st["country"] == "germany" and st.get("gov") == "nazism":
        rows.append([KeyboardButton("⚫ تصمیم ویژه")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def kb_internal():
    return kb_internal_for(0) if False else ReplyKeyboardMarkup([
        [KeyboardButton("📢 تبلیغات دولتی"),KeyboardButton("🏥 خدمات درمانی")],
        [KeyboardButton("📚 آموزش عمومی"),KeyboardButton("💰 یارانه")],
        [KeyboardButton("🕵️ نظارت بر مردم")],
        [KeyboardButton("🔙 منو")]],resize_keyboard=True)

async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    last_action = int(gget(f"last_action_{uid}", "0") or st["turn"])
    turns_since = st["turn"] - last_action
    t = (f"🏛️ *امور کشور {COUNTRIES[st['country']]['n']}*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n"
         f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}\n")
    if st.get("protest"):
        t += f"\n🔥 *اعتراض فعال* ({st.get('protest_t',0)} نوبت مانده)"
    if turns_since >= 15:
        t += f"\n⚠️ *{turns_since} نوبت از آخرین اقدام گذشته! رضایت در حال افت.*"
    t += "\n\n👇 اقدامات داخلی (رضایت +)"
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")

async def _do_internal_action(update, ctx, cost, sat, msg):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    if not pay(uid, money=cost):
        await update.message.reply_text(f"❌ نیاز: {cost}💰")
        return
    sset(uid, happiness=min(100, st["happiness"]+sat))
    gset(f"last_action_{uid}", str(st["turn"]))
    await update.message.reply_text(msg, reply_markup=kb_main())

# ─── ۶. تصمیم ویژه (بدون افشای هولوکاست) ───
async def on_holocaust(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["country"] != "germany" or st.get("gov") != "nazism":
        await update.message.reply_text("❌ در دسترس نیست.")
        return
    if not pay(uid, money=3000):
        await update.message.reply_text("❌ ۳۰۰۰💰 لازمه.")
        return
    sset(uid,
         money=st["money"]+5000,
         steel=st["steel"]+200,
         happiness=max(0, st["happiness"]-20),
         manpower=int(st["manpower"]*0.9))
    add_effect(uid, "special", 5)
    add_effect(uid, "holocaust", 5)
    msg = (f"⚫ *تصمیم ویژه*\n\n"
           f"اقدامات گسترده‌ای علیه گروه‌های خاص آغاز شد. "
           f"اخبار آن در سراسر جهان پیچید.\n\n"
           f"📈 اقتصاد: +۵۰۰۰💰 + ۲۰۰⚙️\n"
           f"📉 رضایت: -۲۰")
    add_news(st["turn"], "special", msg)
    try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
    except: pass
    await update.message.reply_text(msg, reply_markup=kb_main(), parse_mode="Markdown")

# ─── ۷. init_fact بدون کارخونه نظامی ───
def init_fact(uid):
    conn = db()
    for k in ["steel_mill","coal_mine","refinery","food_processing","water_system"]:
        conn.execute("INSERT OR IGNORE INTO factories(user_id,fkey,level) VALUES(?,?,1)",
            (uid, k))
    conn.commit(); conn.close()

# ─── ۸. on_fact فیلتر کارخونه‌های حذف‌شده ───
async def on_fact(update, ctx):
    uid = update.effective_user.id
    lines = ["🏭 *کارخونه‌های استخراج*","━━━━━━━━━━━━━━━━"]
    valid = []
    for f in get_fact(uid):
        if f["fkey"] not in PROJECTS:
            continue
        p = PROJECTS.get(f["fkey"],{})
        lines.append(f"{p.get('n', f['fkey'])} — سطح {f['level']}")
        valid.append(f)
    if not valid:
        lines.append("(هنوز کارخونه‌ای نداری)")
    lines.append("\n👇 برای ارتقا، روی کارخونه بزن")
    ctx.user_data["screen"] = "fact"
    rows = []; row = []
    for f in valid:
        p = PROJECTS.get(f["fkey"],{})
        row.append(KeyboardButton(p.get("n", f["fkey"])))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    await update.message.reply_text("\n".join(lines),
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True), parse_mode="Markdown")

# ─── ۹. نوبت بیشتر برای ارتقا ───
def factory_upgrade_time(level):
    return {1:3, 2:5, 3:7, 4:10}.get(level, 10)

# ─── ۱۰. سیستم neglect در process_turn ───
_old_pt5 = process_turn

def process_turn(uid):
    res = _old_pt5(uid)
    if not res: return res
    st = get_state(uid)
    if not st: return res
    last_action = int(gget(f"last_action_{uid}", "0") or 0)
    if last_action == 0:
        gset(f"last_action_{uid}", str(st["turn"]))
    else:
        if st["turn"] - last_action >= 15:
            sset(uid, happiness=max(0, st["happiness"]-3))
    return res

# ─── ۱۱. راه‌اندازی اولیه neglect برای بازیکن جدید ───
_old_on_country_pick5 = on_country_pick

async def on_country_pick(update, ctx):
    await _old_on_country_pick5(update, ctx)
    uid = update.effective_user.id
    st = get_state(uid)
    if st:
        gset(f"last_action_{uid}", str(st["turn"]))
    return

# ─── ۱۲. hook روی روتر برای اقدامات جدید ───
_old_on_text5 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text5(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "📢 تبلیغات دولتی":
        await _do_internal_action(update, ctx, 500, 5,
            "📢 *تبلیغات دولتی*\nرسانه‌های کشور در خدمت دولت قرار گرفتند. +۵ رضایت")
        return
    if text == "🏥 خدمات درمانی":
        await _do_internal_action(update, ctx, 800, 7,
            "🏥 *خدمات درمانی*\nبیمارستان‌ها و درمانگاه‌های جدید افتتاح شدند. +۷ رضایت")
        return
    if text == "📚 آموزش عمومی":
        await _do_internal_action(update, ctx, 600, 6,
            "📚 *آموزش عمومی*\nمدارس و دانشگاه‌های جدید گسترش یافتند. +۶ رضایت")
        return
    if text == "💰 یارانه":
        await _do_internal_action(update, ctx, 1000, 8,
            "💰 *یارانه*\nکمک مستقیم به خانواده‌ها پرداخت شد. +۸ رضایت")
        return
    if text == "⚫ تصمیم ویژه":
        await on_holocaust(update, ctx); return
    return await _old_on_text5(update, ctx)

# ─── ۱۳. تجارت: حذف «مرحله ۱/۳/۴» ───
async def on_trade(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    ctx.user_data["tr_step"] = "give"
    await update.message.reply_text(
        f"📦 *تجارت*\n💰{fmt(st['money'])} 🍞{fmt(st['food'])} ⚙️{fmt(st['steel'])}\n\n"
        f"💱 چی می‌دی؟",
        reply_markup=kb_trade(), parse_mode="Markdown")# ═══════════════════════════════════════════════════════════════
#  🩹 پچ ۴ — اتم تو ارتش، بدون منوی جدا
# ═══════════════════════════════════════════════════════════════

# ─── کیبورد اصلی بدون اتم ───
def kb_main():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 اقتصاد"),KeyboardButton("⚔️ ارتش")],
        [KeyboardButton("🔬 تحقیقات"),KeyboardButton("🏭 کارخونه‌ها")],
        [KeyboardButton("🤝 دیپلماسی"),KeyboardButton("📦 تجارت")],
        [KeyboardButton("🎯 حمله"),KeyboardButton("🕵️ جاسوسی")],
        [KeyboardButton("💵 مالیات"),KeyboardButton("🏛️ امور کشور")],
        [KeyboardButton("📊 آمار کامل")]],resize_keyboard=True)

# ─── کیبورد ارتش داینامیک ───
def kb_army_for(uid):
    st = get_state(uid)
    if not st:
        return kb_army()
    rows = [
        [KeyboardButton("🪖 سرباز"),KeyboardButton("🛡️ تانک")],
        [KeyboardButton("✈️ جنگنده"),KeyboardButton("🚀 جت")],
        [KeyboardButton("🚢 کشتی"),KeyboardButton("🎯 موشک")],
        [KeyboardButton("💣 بمب‌افکن"),KeyboardButton("🛡️ پدافند")],
        [KeyboardButton("✈️ بمباران"),KeyboardButton("📋 خدمت اجباری")],
    ]
    # دکمه اتم - شرط:
    # ۱. نوبت >= ATOMIC_UNLOCK
    # ۲. یا کشور آلمان/آمریکا، یا اتم قبلاً استفاده شده
    turn = st["turn"]
    can_show = False
    if turn >= ATOMIC_UNLOCK:
        if st["country"] in ("germany", "usa"):
            can_show = True
        elif gget("atomic_used") == "true":
            can_show = True
    if can_show:
        rows.append([KeyboardButton("☢️ پروژه اتمی")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

# ─── on_army با کیبورد داینامیک ───
async def on_army(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    await update.message.reply_text(
        f"⚔️ *ارتش {COUNTRIES[st['country']]['n']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚔️ قدرت حمله: {fmt(calc_power(uid,'attack'))}\n"
        f"🛡️ قدرت دفاع: {fmt(calc_power(uid,'defense'))}\n"
        f"🪖 سرباز: {fmt(st['soldiers'])}\n"
        f"🛡 پدافند: {fmt(get_aa_power(uid))}",
        reply_markup=kb_army_for(uid), parse_mode="Markdown")

# ─── on_atomic جدید — بدون شرط ادمین برای باز شدن ───
async def on_atomic(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    # شرط اصلی: نوبت >= ۱۰۷۷
    if st["turn"] < ATOMIC_UNLOCK:
        await update.message.reply_text(
            f"🔒 *پروژه اتمی*\n\nهنوز باز نشده.\n"
            f"باز شدن: نوبت {ATOMIC_UNLOCK}\n"
            f"الان: نوبت {st['turn']}\n"
            f"مانده: {ATOMIC_UNLOCK - st['turn']} نوبت",
            parse_mode="Markdown")
        return
    # شرط دوم: آلمان/آمریکا یا اولین استفاده شده
    if st["country"] not in ("germany", "usa") and gget("atomic_used") != "true":
        await update.message.reply_text(
            "🔒 این پروژه فقط برای آلمان و آمریکا در دسترس است.\n"
            "بعد از اولین استفاده در جهان، برای همه باز می‌شود.")
        return
    stage = st.get("atomic_stage", 0)
    if stage >= 3:
        await update.message.reply_text(
            f"☢️ *بمب اتمی آماده!*\n"
            f"تعداد بمب: {st.get('atomic_bombs',0)}\n\n"
            f"آماده استفاده از طریق منوی بمباران یا ادمین.",
            reply_markup=kb_army_for(uid), parse_mode="Markdown")
        return
    s = ATOMIC_STAGES[stage]
    await update.message.reply_text(
        f"☢️ *پروژه اتمی*\n"
        f"مرحله {stage+1}/3: {s['n']}\n\n"
        f"⏱️ {s['t']} نوبت\n"
        f"💰 {s['m']}\n⚙️ {s['s']}\n🛢️ {s['o']}\n\n"
        f"برای شروع، دکمه «☢️ شروع مرحله» را بزن.",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("☢️ شروع مرحله")],
            [KeyboardButton("🔙 منو")]],
            resize_keyboard=True), parse_mode="Markdown")

async def on_atomic_start(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    if st["turn"] < ATOMIC_UNLOCK:
        await update.message.reply_text("🔒 هنوز باز نشده.")
        return
    if st["country"] not in ("germany", "usa") and gget("atomic_used") != "true":
        await update.message.reply_text("🔒 در دسترس نیست.")
        return
    stage = st.get("atomic_stage", 0)
    if stage >= 3: return
    s = ATOMIC_STAGES[stage]
    if not pay(uid, money=s["m"], steel=s["s"], oil=s["o"]):
        await update.message.reply_text("❌ منابع کافی نیست.")
        return
    sset(uid, atomic_t=s["t"])
    await update.message.reply_text(
        f"✅ {s['n']} شروع شد! ({s['t']} نوبت)",
        reply_markup=kb_army_for(uid))

# ─── hook روتر ───
_old_on_text4 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text4(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    # دکمه‌های اتم جدید
    if text == "☢️ پروژه اتمی":
        await on_atomic(update, ctx); return
    if text == "☢️ شروع مرحله":
        await on_atomic_start(update, ctx); return
    # منوی قدیمی حذف شده
    if text == "☢️ اتم":
        await update.message.reply_text(
            "ℹ️ این گزینه به بخش «⚔️ ارتش» منتقل شد.")
        return
    return await _old_on_text4(update, ctx)

# ─── وقتی اتم استفاده شد، پیام به همه + باز شدن برای همه ───
def use_atomic(uid, target_uid):
    st = get_state(uid); ts = get_state(target_uid)
    if not st or not ts: return "❌ خطا"
    if st.get("atomic_bombs", 0) <= 0:
        return "❌ بمب اتمی نداری."
    sset(uid, atomic_bombs=st["atomic_bombs"]-1)
    sset(target_uid, happiness=max(0, ts["happiness"]//2),
         soldiers=int(ts["soldiers"]*0.5))
    add_effect(target_uid, "no_attack", 3)
    first_time = (gget("atomic_used") != "true")
    gset("atomic_used", "true")
    add_news(st["turn"], "atomic",
        f"☢️ اولین بمب اتمی تاریخ توسط {COUNTRIES[st['country']]['n']} "
        f"بر فراز پایتخت {COUNTRIES[ts['country']]['n']} منفجر شد.")
    # اگه اولین بار بود، همه رو آگاه کن
    if first_time:
        for p in all_players():
            add_news(int(gget("turn","1")), f"atom_open_{p['uid']}",
                f"☢️ اولین بمب اتم جهان استفاده شد! "
                f"پروژه اتمی برای همه کشورها باز شد.")
    return f"☢️ بمب اتمی {COUNTRIES[ts['country']]['n']} را هدف گرفت."

# ─── تحویل پیام باز شدن اتم ───
_old_deliver = deliver_pending

async def deliver_pending(ctx):
    for p in all_players():
        uid = p["uid"]
        key = f"msg_read_{uid}"
        last_read = int(gget(key, "0") or 0)
        conn = db()
        rows = conn.execute(
            "SELECT * FROM news WHERE id>? AND "
            "(cat=? OR cat=? OR cat=? OR cat=? OR cat=? OR cat=?) ORDER BY id",
            (last_read, f"spy_ok_{uid}", f"spy_fail_{uid}",
             f"spy_caught_{uid}", f"ally_war_{uid}",
             f"conquest_{uid}", f"atom_open_{uid}")).fetchall()
        conn.close()
        for r in rows:
            try:
                if r["cat"].startswith("spy_ok_"):
                    await ctx.bot.send_message(uid,
                        f"✅ *جاسوسی موفق!*\n━━━━━━━━━━━━━━━━\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_fail_"):
                    await ctx.bot.send_message(uid,
                        f"❌ *جاسوس لو رفت!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_caught_"):
                    await ctx.bot.send_message(uid,
                        f"🚨 *هشدار امنیتی!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("ally_war_"):
                    await ctx.bot.send_message(uid,
                        f"⚠️ *هشدار اتحاد!*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                elif r["cat"].startswith("conquest_"):
                    await ctx.bot.send_message(uid,
                        f"💀 *اطلاعیه*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                elif r["cat"].startswith("atom_open_"):
                    await ctx.bot.send_message(uid,
                        f"☢️ *اطلاعیه مهم*\n\n{r['text']}\n\n"
                        f"از این پس، پروژه اتمی در بخش «⚔️ ارتش» برای تو هم باز است.",
                        parse_mode="Markdown")
                last_read = r["id"]
            except: pass
        gset(key, str(last_read))# ═══════════════════════════════════════════════════════════════
#  🩹 پچ ۳ — فیکس نهایی
# ═══════════════════════════════════════════════════════════════

# ─── ۱. نازیسم در کیبورد انتخاب حکومت ───
def kb_gov():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👑 پادشاهی مطلقه"),KeyboardButton("👑 پادشاهی مشروطه")],
        [KeyboardButton("🗳️ جمهوری ریاستی"),KeyboardButton("🗳️ جمهوری پارلمانی")],
        [KeyboardButton("🚩 فاشیسم"),KeyboardButton("⚫ نازیسم")],
        [KeyboardButton("🚩 کمونیسم"),KeyboardButton("🚩 تک‌حزبی")],
        [KeyboardButton("⚙️ دیکتاتوری نظامی"),KeyboardButton("⚙️ دیکتاتوری شخصی")],
        [KeyboardButton("🕊️ دموکراسی لیبرال"),KeyboardButton("🕊️ دموکراسی اجتماعی")],
        [KeyboardButton("⚖️ تئوکراسی")]],
        resize_keyboard=True,one_time_keyboard=True)

# ─── ۲. on_gov_pick با نازیسم ───
async def on_gov_pick(update, ctx):
    if ctx.user_data.get("wait") != "gov": return
    text = update.message.text.strip()
    gmap = {
        "👑 پادشاهی مطلقه":"absolute_monarchy",
        "👑 پادشاهی مشروطه":"constitutional_monarchy",
        "🗳️ جمهوری ریاستی":"presidential_republic",
        "🗳️ جمهوری پارلمانی":"parliamentary_republic",
        "🚩 فاشیسم":"fascist",
        "⚫ نازیسم":"nazism",
        "🚩 کمونیسم":"communism",
        "🚩 تک‌حزبی":"single_party",
        "⚙️ دیکتاتوری نظامی":"military_dictatorship",
        "⚙️ دیکتاتوری شخصی":"personal_dictatorship",
        "🕊️ دموکراسی لیبرال":"liberal_democracy",
        "🕊️ دموکراسی اجتماعی":"social_democracy",
        "⚖️ تئوکراسی":"theocracy",
    }
    if text not in gmap: return
    uid = update.effective_user.id
    pset(uid, gov=gmap[text])
    ctx.user_data["wait"] = None
    st = get_state(uid)
    extra = ""
    if gmap[text] == "nazism":
        extra = "\n\n⚫ *رژیم نازی*\nاز منوی امور کشور، گزینه هولوکاست فعال شد."
    await update.message.reply_text(f"✅{extra}\n\n{render_dash(st)}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── ۳. اتم: هیچ‌کس (حتی ادمین) قبل نوبت ۱۰۷۷ نمی‌تونه ───
async def on_atomic(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    # ⛔ هیچ استثنایی نیست — حتی ادمین
    if st["turn"] < ATOMIC_UNLOCK:
        await update.message.reply_text(
            f"🔒 *پروژه اتمی*\n\nهنوز باز نشده.\n"
            f"باز شدن: نوبت {ATOMIC_UNLOCK}\n"
            f"الان: نوبت {st['turn']}\n"
            f"مانده: {ATOMIC_UNLOCK - st['turn']} نوبت",
            parse_mode="Markdown")
        return
    # فقط آلمان و آمریکا
    if st["country"] not in ["germany","usa"] and gget("atomic_used") != "true":
        await update.message.reply_text("🔒 این پروژه در دسترس نیست.")
        return
    stage = st.get("atomic_stage", 0)
    if stage >= 3:
        await update.message.reply_text(
            f"☢️ *بمب اتمی آماده!*\nتعداد بمب: {st.get('atomic_bombs',0)}\n\n"
            f"برای استفاده: آیتم `بمب اتم` (فقط ادمین‌ها)",
            reply_markup=kb_main(), parse_mode="Markdown")
        return
    s = ATOMIC_STAGES[stage]
    await update.message.reply_text(
        f"☢️ *پروژه اتمی*\nمرحله {stage}/3\n{s['n']}\n"
        f"⏱️ {s['t']} نوبت\n💰{s['m']} ⚙️{s['s']} 🛢️{s['o']}",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("☢️ شروع مرحله")],[KeyboardButton("🔙 منو")]],
            resize_keyboard=True), parse_mode="Markdown")

# ─── ۴. تحقیق زمان‌دار ───
_old_on_text3 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text3(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    st = get_state(uid)
    if not st:
        return await _old_on_text3(update, ctx)
    screen = ctx.user_data.get("screen", "menu")
    # ─── فیکس تحقیق زمان‌دار ───
    if screen.startswith("research_"):
        cat = screen.split("_", 1)[1]
        tree = get_tree(st["country"], cat)
        researched = get_res(uid, cat)
        # اگه داره تحقیق می‌کنه
        for i, item in enumerate(tree):
            if len(item) < 7: continue
            name, power, cost, build, steel, oil, desc = item
            if name == text:
                if i == 0:
                    await update.message.reply_text("این مدل از اول باز است.")
                    return
                if name in researched:
                    await update.message.reply_text("قبلاً تحقیق شده.")
                    return
                # چک نکنه تو صف هست
                in_q = any(p["category"] == "research_pending" and
                           p["model"] == f"{cat}:{name}" for p in get_pq(uid))
                if in_q:
                    await update.message.reply_text("این مدل در حال تحقیق است.")
                    return
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰")
                    return
                # صف تحقیق با زمان
                conn = db()
                conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
                    (uid, "research_pending", f"{cat}:{name}", 1, build))
                conn.commit(); conn.close()
                await update.message.reply_text(
                    f"🔬 *{name}* در صف تحقیق!\n"
                    f"⏱️ زمان: {build} نوبت\n"
                    f"💰 هزینه: {cost}",
                    reply_markup=kb_main(), parse_mode="Markdown")
                return
    # ─── فیکس کارخونه: زمان‌دار ───
    if screen == "fact":
        for f in get_fact(uid):
            p = PROJECTS.get(f["fkey"], {})
            if p.get("n") == text:
                lvl = f["level"]
                if lvl >= 5:
                    await update.message.reply_text("🏆 حداکثر سطح.")
                    return
                costs = {1:500, 2:1200, 3:2500, 4:5000}
                cost = costs.get(lvl, 0)
                # چک زمان
                in_q = any(q["pkey"] == f"fact_{f['fkey']}_{lvl}" for q in get_projq(uid))
                if in_q:
                    await update.message.reply_text("این ارتقا در حال ساخت است.")
                    return
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰")
                    return
                # صف ارتقا با زمان (۳ نوبت)
                add_projq(uid, f"fact_{f['fkey']}_{lvl}", 3)
                await update.message.reply_text(
                    f"⚙️ ارتقای {p.get('n',f['fkey'])} در صف\n⏱️ زمان: ۳ نوبت\n💰 هزینه: {cost}",
                    reply_markup=kb_main())
                return
    # ─── فیکس خدمت اجباری: زمان‌دار ───
    if text == "📋 خدمت اجباری":
        if not pay(uid, money=1000):
            await update.message.reply_text("❌ ۱۰۰۰💰 لازمه.")
            return
        add_projq(uid, f"conscription_{uid}", 2)
        await update.message.reply_text(
            "📋 خدمت اجباری در صف (۲ نوبت)\n"
            "پس از ۲ نوبت: -۱۵ رضایت، +۵۰۰ نیرو",
            reply_markup=kb_main())
        return
    # ─── فیکس بمباران: زمان‌دار ───
    if text in ("🏭 بمباران کارخونه","🔧 بمباران تجهیزات",
                "💀 ترور فرمانده","🛢️ بمباران پالایشگاه"):
        ctx.user_data["bomb_pending"] = text
        ctx.user_data["wait"] = "bomb_target"
        await update.message.reply_text("🎯 کشور هدف 👇", reply_markup=kb_targets(uid))
        return
    # ادامه روتر اصلی
    return await _old_on_text3(update, ctx)

# ─── ۵. on_bomb_target زمان‌دار ───
async def on_bomb_target(update, ctx):
    if ctx.user_data.get("wait") != "bomb_target": return
    text = update.message.text.strip()
    if text not in CMAP: return
    tk = CMAP[text]
    uid = update.effective_user.id
    st = get_state(uid)
    tu = find_country(tk)
    if not tu:
        await update.message.reply_text("❌"); return
    # ذخیره در صف با زمان ۱ نوبت
    bomb_kind_map = {
        "🏭 بمباران کارخونه":"factory",
        "🔧 بمباران تجهیزات":"equip",
        "💀 ترور فرمانده":"assassin",
        "🛢️ بمباران پالایشگاه":"refinery",
    }
    btext = ctx.user_data.get("bomb_pending")
    kind = bomb_kind_map.get(btext, "factory")
    # هزینه
    if not pay(uid, money=500, oil=30):
        await update.message.reply_text("❌ نیاز: ۵۰۰💰 + ۳۰🛢️")
        ctx.user_data["wait"]=None; return
    # صف بمباران
    conn = db()
    conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
        (uid, "bomb_pending", f"{kind}:{tu}", 1, 1))
    conn.commit(); conn.close()
    await update.message.reply_text(
        f"✈️ بمباران {COUNTRIES[tk]['n']} در صف\n⏱️ زمان: ۱ نوبت",
        reply_markup=kb_main())
    ctx.user_data["wait"]=None
    ctx.user_data["bomb_pending"]=None

# ─── ۶. کیبورد امور کشور با هولوکاست ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب اعتراض")])
    rows.append([KeyboardButton("🕵️ نظارت بر مردم")])
    if st and st["country"] == "germany" and st.get("gov") == "nazism":
        rows.append([KeyboardButton("⚫ هولوکاست")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    t = (f"🏛️ *امور کشور {COUNTRIES[st['country']]['n']}*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n"
         f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}\n")
    if st.get("protest"):
        t += f"\n🔥 *اعتراض فعال* ({st.get('protest_t',0)} نوبت مانده)"
    if st["country"] == "germany" and st.get("gov") == "nazism":
        t += "\n⚫ *رژیم نازی فعال — هولوکاست در دسترس*"
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")

# ─── ۷. هولوکاست ───
async def on_holocaust(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["country"] != "germany" or st.get("gov") != "nazism":
        await update.message.reply_text("❌ این گزینه فقط برای آلمان نازی است.")
        return
    if not pay(uid, money=3000):
        await update.message.reply_text("❌ ۳۰۰۰💰 لازمه.")
        return
    sset(uid,
         money=st["money"]+5000,
         steel=st["steel"]+200,
         happiness=max(0, st["happiness"]-20),
         manpower=int(st["manpower"]*0.9))
    add_effect(uid, "holocaust", 5)
    msg = (f"⚫ *هولوکاست در آلمان*\n\n"
           f"رژیم نازی برنامه پاکسازی نژادی را آغاز کرد. یهودیان، کولی‌ها، "
           f"معلولان و بیماران روانی به اردوگاه‌های کار اجباری منتقل شدند.\n\n"
           f"💰 اقتصاد: +۵۰۰۰\n⚙️ فولاد: +۲۰۰\n😊 رضایت: -۲۰")
    add_news(st["turn"], "holocaust", msg)
    try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
    except: pass
    await update.message.reply_text(msg, reply_markup=kb_main(), parse_mode="Markdown")

# ─── ۸. fیکس: پردازش تحقیقات و بمباران تو process_turn ───
_old_process_turn2 = process_turn

def process_turn(uid):
    st = get_state(uid)
    if not st: return None
    c = COUNTRIES[st["country"]]
    mult = 2.0 if is_vip(uid) else 1.0
    upd = {}
    tm = st["tax"] / 20.0
    upd["money"] = st["money"] + c["bm"]*tm*mult
    upd["food"] = st["food"] + c["bf"]*mult
    upd["water"] = st["water"] + c["bf"]*0.5*mult
    upd["steel"] = st["steel"] + c["bs"]*mult
    upd["oil"] = st["oil"] + c["bo"]*mult
    upd["coal"] = st["coal"] + c["bc"]*mult
    upd["manpower"] = st["manpower"] + 50*mult
    conn = db()
    bombs = conn.execute("SELECT * FROM bombing WHERE target_uid=?", (uid,)).fetchall()
    bf = 0.5 if any(b["effect"]=="factory" for b in bombs) else 1.0
    br = 0.5 if any(b["effect"]=="refinery" for b in bombs) else 1.0
    for b in bombs:
        t = b["turns"] - 1
        if t <= 0: conn.execute("DELETE FROM bombing WHERE id=?", (b["id"],))
        else: conn.execute("UPDATE bombing SET turns=? WHERE id=?", (t, b["id"]))
    conn.commit(); conn.close()
    for f in get_fact(uid):
        p = PROJECTS.get(f["fkey"])
        if p and p["eff"] in ("steel","oil","coal","food","water","money"):
            r = p["eff"]
            fac = 1.0
            if r == "oil": fac = br
            if r in ("steel","coal"): fac = bf
            upd[r] = upd.get(r, st.get(r, 0)) + p["v"]*f["level"]*mult*fac
    hap = st["happiness"] + calc_hap_delta(uid, st)
    hap = max(0, min(100, hap))
    upd["happiness"] = hap
    upd.update(check_protest(uid, st))
    if st.get("suppress_cd", 0) > 0:
        nc = st["suppress_cd"] - 1
        upd["suppress_cd"] = nc
        if nc == 0:
            upd["happiness"] = max(0, upd.get("happiness", hap) - 5)
    conn = db()
    for it in conn.execute("SELECT * FROM items WHERE turns_left>0").fetchall():
        t = it["turns_left"] - 1
        if t <= 0: conn.execute("DELETE FROM items WHERE id=?", (it["id"],))
        else: conn.execute("UPDATE items SET turns_left=? WHERE id=?", (t, it["id"]))
    conn.commit(); conn.close()
    # صف تولید + تحقیق زمان‌دار
    conn = db()
    for item in get_pq(uid):
        t = item["turns"] - 1
        if t <= 0:
            if item["category"] == "research_pending":
                parts = item["model"].split(":", 1)
                if len(parts) == 2:
                    mark_res(uid, parts[0], parts[1])
                    add_news(st["turn"], "research",
                        f"🔬 {parts[1]} در {c['n']} تحقیق شد!")
            elif item["category"] == "bomb_pending":
                parts = item["model"].split(":", 1)
                if len(parts) == 2:
                    kind = parts[0]
                    try: target_uid = int(parts[1])
                    except: target_uid = 0
                    if target_uid:
                        do_bombing(uid, target_uid, kind)
            else:
                add_army(uid, item["category"], item["model"], item["qty"])
            conn.execute("DELETE FROM pq WHERE id=?", (item["id"],))
        else:
            conn.execute("UPDATE pq SET turns=? WHERE id=?", (t, item["id"]))
    # صف پروژه (ارتقا کارخونه + خدمت اجباری)
    for p in get_projq(uid):
        t = p["turns"] - 1
        if t <= 0:
            pk = p["pkey"]
            if pk.startswith("fact_"):
                parts = pk.split("_")
                if len(parts) == 3:
                    fkey = parts[1]
                    conn.execute("UPDATE factories SET level=level+1 WHERE user_id=? AND fkey=?",
                        (uid, fkey))
            elif pk.startswith("conscription_"):
                st2 = get_state(uid)
                if st2:
                    sset(uid, happiness=max(0, st2["happiness"]-15),
                         manpower=st2["manpower"]+500)
            else:
                mark_proj(uid, pk)
            conn.execute("DELETE FROM projq WHERE id=?", (p["id"],))
        else:
            conn.execute("UPDATE projq SET turns=? WHERE id=?", (t, p["id"]))
    for s in conn.execute("SELECT * FROM spies WHERE from_id=? AND status='pending'",
        (uid,)).fetchall():
        t = s["turns"] - 1
        if t <= 0:
            resolve_spy(uid, s["to_id"])
            conn.execute("UPDATE spies SET status='done' WHERE id=?", (s["id"],))
        else:
            conn.execute("UPDATE spies SET turns=? WHERE id=?", (t, s["id"]))
    conn.commit(); conn.close()
    if st.get("atomic_t", 0) > 0:
        t = st["atomic_t"] - 1
        if t <= 0:
            ns = st.get("atomic_stage", 0) + 1
            upd["atomic_stage"] = ns
            upd["atomic_t"] = 0
            if ns >= 3:
                upd["atomic_bombs"] = st.get("atomic_bombs", 0) + 1
        else:
            upd["atomic_t"] = t
    nd = next_date(st["game_date"])
    upd["game_date"] = nd
    upd["turn"] = st["turn"] + 1
    upd["last_turn"] = datetime.utcnow().isoformat()
    ev = []
    if nd in EVENTS:
        ev.append(EVENTS[nd])
        add_news(st["turn"], "hist", EVENTS[nd])
    sset(uid, **upd)
    return {"turn": st["turn"]+1, "date": nd, "ev": ev}# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — حذف neglect، ۱ اقدام از هر بخش در نوبت
# ═══════════════════════════════════════════════════════════════

# دسته‌بندی اقدامات
ACTION_SECTION = {
    # امور مردم
    "🏥 بیمارستان جدید": "people",
    "📚 مدرسه جدید": "people",
    "💧 سیستم آب": "people",
    "🏠 مسکن عمومی": "people",
    "🍞 سهمیه غذا": "people",
    # امور حکومت
    "📜 اصلاحات مدنی": "gov",
    "⚖️ اصلاح قضایی": "gov",
    "💰 مبارزه با فساد": "gov",
    "🏛️ قانون اساسی": "gov",
    "📻 تبلیغات دولتی": "gov",
    # دولت
    "💼 برنامه اشتغال": "state",
    "🏗️ زیرساخت": "state",
    "🎓 دانشگاه ملی": "state",
    # مشکلات
    "🚨 مبارزه با جرم": "problems",
    # تورم
    "📉 کنترل قیمت‌ها": "inflation",
}

def can_do_action(uid, action):
    st = get_state(uid)
    if not st: return False, "❌ خطا"
    info = INTERNAL_ACTIONS.get(action)
    if not info: return False, "❌ اقدام نامعتبر"
    section = ACTION_SECTION.get(action, "misc")
    # سقف کل
    count = get_action_count(uid, action)
    if count >= info["max"]:
        return False, f"❌ این اقدام حداکثر {info['max']} بار قابل انجام است."
    # چک کن همین اقدام الان تو صف نباشه
    in_q = any(p["category"] == "internal_action" and p["model"] == action
               for p in get_pq(uid))
    if in_q:
        return False, "⏳ این اقدام در حال اجراست."
    # چک کن این نوبت تو این بخش اقدامی نکرده
    key = f"section_{section}_{uid}"
    last_section = int(gget(key, "0") or 0)
    if last_section == st["turn"]:
        return False, "⚠️ در این نوبت یک اقدام از این بخش انجام دادی. بخش دیگه‌ای یا نوبت بعد."
    # منابع
    if not is_admin(uid):
        if st["money"] < info["money"]:
            return False, f"❌ نیاز: {info['money']}💰 (داری {fmt(st['money'])})"
        if st["steel"] < info["steel"]:
            return False, f"❌ نیاز: {info['steel']}⚙️ (داری {fmt(st['steel'])})"
    return True, info

async def on_int_action(update, ctx, action):
    uid = update.effective_user.id
    ok, data = can_do_action(uid, action)
    if not ok:
        await update.message.reply_text(data)
        return
    info = data
    section = ACTION_SECTION.get(action, "misc")
    if not pay(uid, money=info["money"], steel=info["steel"]):
        await update.message.reply_text("❌ منابع کافی نیست.")
        return
    conn = db()
    conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
        (uid, "internal_action", action, 1, info["turns"]))
    conn.commit(); conn.close()
    gset(f"section_{section}_{uid}", str(get_state(uid)["turn"]))
    count = get_action_count(uid, action) + 1
    section_fa = {
        "people": "امور مردم", "gov": "امور حکومت",
        "state": "دولت", "problems": "مشکلات", "inflation": "تورم",
    }.get(section, "سایر")
    await update.message.reply_text(
        f"🏛️ *{action}*\n"
        f"📁 بخش: {section_fa}\n\n"
        f"🔨 در حال اجرا\n"
        f"⏱️ {info['turns']} نوبت دیگر\n"
        f"💰 {info['money']} | ⚙️ {info['steel']}\n"
        f"📊 رضایت پس از تکمیل: +{info['hap']}\n"
        f"🔢 اجرای {count} از {info['max']}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── حذف neglect از process_turn ───
_old_process_turn_neg = process_turn

def process_turn(uid):
    # چک نکن neglect رو
    return _old_process_turn_neg(uid)

# ─── hook روتر ───
_old_on_text_neg = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text_neg(update, ctx)
    text = update.message.text.strip()
    if text in INTERNAL_ACTIONS:
        await on_int_action(update, ctx, text); return
    return await _old_on_text_neg(update, ctx)

# ─── on_internal بدون هشدار neglect ───
async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    t = (f"🏛️ *امور کشور*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n")
    if st.get("protest"):
        t += f"🔥 اعتراض فعال ({st.get('protest_t',0)} نوبت)"
    t += ("\n\n💡 *در هر نوبت، از هر بخش یک اقدام می‌تونی بکنی*\n\n"
          "👇 بخش مورد نظر:")
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")# ═══════════════════════════════════════════════════════════════
#  🩹 پچ باگ‌ها (بازنویسی توابع)
# ═══════════════════════════════════════════════════════════════

TARGET_FREE_ITEMS = ("carpet_bomb", "war_speech", "war_storm", "revive",
                     "god_shield", "invisible", "double_attack", "lock_on",
                     "revenge", "seize_power")

# ─── پچ ۱: پیشنهاد صلح حالا جنگ رو تموم می‌کنه ───
async def on_neg_resp(update, ctx, nid, acc):
    uid = update.effective_user.id
    conn = db()
    r = conn.execute("SELECT * FROM negs WHERE id=? AND to_id=?", (nid, uid)).fetchone()
    if not r:
        conn.close(); await update.message.reply_text("❌ درخواست پیدا نشد."); return
    r = dict(r)
    conn.execute("UPDATE negs SET status=? WHERE id=?",
        ("accepted" if acc else "rejected", nid))
    if acc and r["kind"] == "nap":
        add_nap(uid, r["from_id"], int(gget("turn","1"))+10)
    if acc and r["kind"] == "cancel_nap":
        cancel_nap(uid, r["from_id"])
    if acc and r["kind"] == "alliance":
        try:
            aid = int(r["payload"])
            conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
        except: pass
    if acc and r["kind"] == "peace":
        from_uid = r["from_id"]; to_uid = uid
        conn.execute("DELETE FROM wars WHERE (atk_uid=? AND def_uid=?) OR (atk_uid=? AND def_uid=?)",
            (from_uid, to_uid, to_uid, from_uid))
        conn.execute("UPDATE states SET war=0 WHERE user_id=?", (from_uid,))
        conn.execute("UPDATE states SET war=0 WHERE user_id=?", (to_uid,))
        fs = get_state(from_uid); ts = get_state(to_uid)
        if fs and ts:
            peace_msg = (f"☮️ *صلح میان {COUNTRIES[fs['country']]['n']} و "
                         f"{COUNTRIES[ts['country']]['n']}*\n\n"
                         f"دو کشور رسماً به مخاصمات پایان دادند.")
            add_news(int(gget("turn","1")), "peace", peace_msg)
            try: await ctx.bot.send_message(NEWS_CH, peace_msg, parse_mode="Markdown")
            except: pass
            try: await ctx.bot.send_message(from_uid, peace_msg, parse_mode="Markdown")
            except: pass
    conn.commit(); conn.close()
    msg = "✅ قبول" if acc else "❌ رد"
    await update.message.reply_text(f"درخواست: {msg}", reply_markup=kb_main())
    try: await ctx.bot.send_message(r["from_id"], f"📩 پاسخ درخواستت: {msg}")
    except: pass

# ─── پچ ۲: آیتم‌های بدون هدف ───
async def apply_item_effect(ctx, uid, item_key, target_uid=None):
    st = get_state(uid)
    if not st: return "❌ خطا"
    c = COUNTRIES[st["country"]]
    result = "✅"
    if item_key in TARGET_FREE_ITEMS:
        if item_key == "carpet_bomb":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], happiness=max(0, ps["happiness"]-10))
            result = "🔥 بمباران قالی — همه دشمنان آسیب دیدند."
        elif item_key == "war_speech":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], money=max(0, ps["money"]*0.5))
            result = "📢 نطق جنگی — ۵۰٪ پول همه به تو رسید."
        elif item_key == "war_storm":
            result = "🌪 طوفان جنگی — همه حملات دشمن عقب رانده شد."
        elif item_key == "revive":
            add_effect(uid, "revive", 999)
            result = "🔄 محافظت مرگ فعال شد."
        elif item_key == "god_shield":
            add_effect(uid, "shield", 60)
            result = "🛡 سپر جان — ۱ ساعت نامیرا."
        elif item_key == "invisible":
            add_effect(uid, "invisible", 30)
            result = "👻 نامرئی — ۳۰ دقیقه."
        elif item_key == "double_attack":
            add_effect(uid, "double_attack", 10)
            result = "⚡ دوبرابر حمله — ۱۰ نوبت."
        elif item_key == "lock_on":
            add_effect(uid, "lock_on", 10)
            result = "🎯 قفل روی حریف — ۱۰ نوبت."
        elif item_key == "revenge":
            add_effect(uid, "revenge", 999)
            result = "💀 انتقام فعال شد."
        elif item_key == "seize_power":
            add_effect(uid, "commander", 10)
            result = f"👑 {c['n']} ۱۰ نوبت فرمانده شد."
        add_news(st["turn"], "item", result)
        return result
    if item_key == "force_exile" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"🗳 {COUNTRIES[ts['country']]['n']} از بازی اخراج شد."
    elif item_key == "censor" and target_uid:
        add_effect(target_uid, "censored", 3)
        result = f"🤐 {COUNTRIES[get_state(target_uid)['country']]['n']} ۳ نوبت سانسور شد."
    elif item_key == "expose" and target_uid:
        result = f"🕵️ اطلاعات {COUNTRIES[get_state(target_uid)['country']]['n']} فاش شد."
    elif item_key == "force_ally" and target_uid:
        aid = get_user_alliance(uid)
        if not aid:
            conn = db()
            cur = conn.execute("INSERT INTO alliances(name,founder) VALUES(?,?)",
                (f"اتحاد {c['n']}", uid))
            aid = cur.lastrowid
            conn.execute("INSERT INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
            conn.commit(); conn.close()
        conn = db()
        conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, target_uid))
        conn.commit(); conn.close()
        result = f"🤝 {COUNTRIES[get_state(target_uid)['country']]['n']} به اتحاد اضافه شد."
    elif item_key == "plunder" and target_uid:
        ts = get_state(target_uid)
        if ts:
            half = ts["money"] // 2
            sset(target_uid, money=ts["money"] - half)
            sset(uid, money=st["money"] + half)
            result = f"💰 {fmt(half)} پول از دشمن غارت شد."
    elif item_key == "tsar_bomb" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"💣 بمب تزار — {COUNTRIES[ts['country']]['n']} نابود شد."
    elif item_key == "nuke_item" and target_uid:
        result = use_atomic(uid, target_uid)
    elif item_key == "bio_weapon" and target_uid:
        add_effect(target_uid, "no_attack", 5)
        result = f"☠️ {COUNTRIES[get_state(target_uid)['country']]['n']} ۵ نوبت نمی‌تونه حمله کنه."
    elif item_key == "ballistic" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"🚀 موشک بالستیک — {COUNTRIES[ts['country']]['n']} از بازی حذف شد."
    add_news(st["turn"], "item", result)
    return result

# ─── پچ ۳: هشدار به اعضای اتحاد در جنگ ───
_old_advance_wars = advance_wars

def advance_wars():
    conn = db()
    wars = conn.execute("SELECT * FROM wars").fetchall()
    conn.close()
    for w in wars:
        au = w["atk_uid"]; du = w["def_uid"]
        ast = get_state(au); dst = get_state(du)
        if not ast or not dst or dst.get("dead"):
            conn = db()
            conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
            conn.commit(); conn.close()
            continue
        t = w["turns"] - 1
        stage = w["stage"]
        if stage == "move" and t <= 0:
            my = calc_power(au, "attack")
            en = calc_power(du, "defense")
            aid_d = get_user_alliance(du)
            if aid_d:
                for m in get_alliance_members(aid_d):
                    if m != du and m != au:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            en += calc_power(m, "defense")
                            add_news(int(gget("turn","1")), f"ally_war_{m}",
                                f"{COUNTRIES[w['attacker']]['n']} به متحد تو "
                                f"{COUNTRIES[w['defender']]['n']} حمله کرد. "
                                f"بر اساس پیمان، در جنگ وارد شدی.")
            aid_a = get_user_alliance(au)
            if aid_a:
                for m in get_alliance_members(aid_a):
                    if m != au and m != du:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            my += calc_power(m, "attack")
                            add_news(int(gget("turn","1")), f"ally_war_{m}",
                                f"متحد تو {COUNTRIES[w['attacker']]['n']} به "
                                f"{COUNTRIES[w['defender']]['n']} حمله کرد. "
                                f"بر اساس پیمان، در جنگ وارد شدی.")
            battle_msg = (f"⚔️ نبرد میان {COUNTRIES[w['attacker']]['n']} و "
                          f"{COUNTRIES[w['defender']]['n']}\n"
                          f"قدرت حمله: {fmt(my)} — قدرت دفاع: {fmt(en)}")
            add_news(int(gget("turn","1")), "battle", battle_msg)
            if my > en:
                for u in get_army(au):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (int(u["count"]*0.85), u["id"]))
                    conn.commit(); conn.close()
                ds = get_state(du)
                if ds:
                    sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5,
                         soldiers=int(ds["soldiers"]*0.5))
                conn = db()
                conn.execute("UPDATE wars SET stage='resolve', turns=1 WHERE id=?",
                    (w["id"],))
                conn.commit(); conn.close()
                add_news(int(gget("turn","1")), "war",
                    f"🏆 {COUNTRIES[w['attacker']]['n']} در نبرد اولیه پیروز شد.")
                if calc_power(du, "defense") < my * 0.2:
                    conquer_country(None, au, du)
            else:
                for u in get_army(au):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (int(u["count"]*0.4), u["id"]))
                    conn.commit(); conn.close()
                conn = db()
                conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
                conn.commit(); conn.close()
                add_news(int(gget("turn","1")), "war",
                    f"💀 حمله {COUNTRIES[w['attacker']]['n']} شکست خورد.")
        elif stage == "resolve":
            ds = get_state(du)
            if ds:
                sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5)
                for u in get_army(du):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (int(u["count"]*0.5), u["id"]))
                    conn.commit(); conn.close()
                conquer_country(None, au, du)
            conn = db()
            conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
            conn.commit(); conn.close()

# ─── پچ ۴: تحویل پیام‌های هشدار اتحاد ───
async def deliver_pending(ctx):
    for p in all_players():
        uid = p["uid"]
        key = f"msg_read_{uid}"
        last_read = int(gget(key, "0") or 0)
        conn = db()
        rows = conn.execute(
            "SELECT * FROM news WHERE id>? AND (cat=? OR cat=? OR cat=? OR cat=? OR cat=?) ORDER BY id",
            (last_read, f"spy_ok_{uid}", f"spy_fail_{uid}",
             f"spy_caught_{uid}", f"ally_war_{uid}", f"conquest_{uid}")).fetchall()
        conn.close()
        for r in rows:
            try:
                if r["cat"].startswith("spy_ok_"):
                    await ctx.bot.send_message(uid,
                        f"✅ *جاسوسی موفق!*\n━━━━━━━━━━━━━━━━\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_fail_"):
                    await ctx.bot.send_message(uid,
                        f"❌ *جاسوس لو رفت!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_caught_"):
                    await ctx.bot.send_message(uid,
                        f"🚨 *هشدار امنیتی!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("ally_war_"):
                    await ctx.bot.send_message(uid,
                        f"⚠️ *هشدار اتحاد!*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                elif r["cat"].startswith("conquest_"):
                    await ctx.bot.send_message(uid,
                        f"💀 *اطلاعیه*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                last_read = r["id"]
            except: pass
        gset(key, str(last_read))

# ─── پچ ۵: on_text wrapper برای آیتم‌های بدون هدف ───
_old_on_text = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text in ITEM_FA and is_admin(uid):
        ik = ITEM_FA[text]
        if ik in TARGET_FREE_ITEMS:
            result = await apply_item_effect(ctx, uid, ik)
            await update.message.reply_text(result, reply_markup=kb_main())
            return
    return await _old_on_text(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ ۲ — تغییرات جدید
# ═══════════════════════════════════════════════════════════════

# ─── ۱. نازیسم به حکومت‌ها ───
GOVS["nazism"] = ("⚫ نازیسم", -5)

# ─── ۲. کیبورد اصلی بدون سخنرانی ───
def kb_main():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 اقتصاد"),KeyboardButton("⚔️ ارتش")],
        [KeyboardButton("🔬 تحقیقات"),KeyboardButton("🏭 کارخونه‌ها")],
        [KeyboardButton("🤝 دیپلماسی"),KeyboardButton("📦 تجارت")],
        [KeyboardButton("🎯 حمله"),KeyboardButton("🕵️ جاسوسی")],
        [KeyboardButton("💵 مالیات"),KeyboardButton("🏛️ امور کشور")],
        [KeyboardButton("☢️ اتم"),KeyboardButton("📊 آمار کامل")]],resize_keyboard=True)

# ─── ۳. کیبورد ارتش با بمباران ───
def kb_army():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🪖 سرباز"),KeyboardButton("🛡️ تانک")],
        [KeyboardButton("✈️ جنگنده"),KeyboardButton("🚀 جت")],
        [KeyboardButton("🚢 کشتی"),KeyboardButton("🎯 موشک")],
        [KeyboardButton("💣 بمب‌افکن"),KeyboardButton("🛡️ پدافند")],
        [KeyboardButton("✈️ بمباران"),KeyboardButton("📋 خدمت اجباری")],
        [KeyboardButton("🔙 منو")]],resize_keyboard=True)

# ─── ۴. کیبورد امور کشور با سرکوب شرطی + هولوکاست ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب اعتراض")])
    rows.append([KeyboardButton("🕵️ نظارت بر مردم")])
    # هولوکاست فقط برای آلمان نازی
    if st and st["country"] == "germany" and st.get("gov") == "nazism":
        rows.append([KeyboardButton("⚫ هولوکاست")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def kb_internal():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🕵️ نظارت بر مردم")],[KeyboardButton("🔙 منو")]],
        resize_keyboard=True)

# ─── ۵. کیبورد تجارت جدید ───
def kb_trade():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 پول"),KeyboardButton("🍞 غذا")],
        [KeyboardButton("💧 آب"),KeyboardButton("⚙️ فولاد")],
        [KeyboardButton("🛢️ نفت"),KeyboardButton("🪨 زغال")],
        [KeyboardButton("👥 نیرو"),KeyboardButton("❌ هیچی")],
        [KeyboardButton("🔙 منو")]],resize_keyboard=True)

# ─── ۶. نمایش تحقیق با جزئیات + زمان ───
async def on_research_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"research_{cat}"
    lines = [f"🔬 *{CAT_N[cat]}*","━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power, cost, build, steel, oil, desc = item
        if i == 0:
            lines.append(f"✅ *{name}* (از اول باز)\n   قدرت: {power} | ⚙️{steel} | 🛢️{oil}")
        elif name in researched:
            lines.append(f"✅ *{name}*\n   قدرت: {power} | ⚙️{steel} | 🛢️{oil}")
        else:
            lines.append(
                f"🔒 *{name}*\n"
                f"   📝 {desc}\n"
                f"   💪 قدرت: {power}\n"
                f"   🔬 تحقیق: {cost}💰 + {build} نوبت\n"
                f"   🏭 ساخت: ⚙️{steel} + 🛢️{oil}"
            )
    lines.append("\n👇 روی مدل بزن تا تحقیق کنی")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

# ─── ۷. نمایش خرید ارتش با جزئیات ───
async def on_army_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"buy_{cat}"
    lines = [CAT_N[cat],"━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power, rc, build, steel, oil, desc = item
        if i == 0 or name in researched:
            pm = power*20+100
            lines.append(
                f"✅ *{name}*\n"
                f"   📝 {desc}\n"
                f"   💪 قدرت: {power}\n"
                f"   💰 هزینه: {pm} + ⚙️{steel} + 🛢️{oil}\n"
                f"   ⏱️ ساخت: {build} نوبت"
            )
        else:
            lines.append(f"🔒 {name} (تحقیق نشده)")
    lines.append("\n👇 روی مدل بزن تا تعداد بپرسی")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

# ─── ۸. امور کشور جدید ───
async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    t = (f"🏛️ *امور کشور {COUNTRIES[st['country']]['n']}*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n")
    if st.get("protest"):
        t += f"\n🔥 *اعتراض فعال* ({st.get('protest_t',0)} نوبت مانده)"
    if st["country"] == "germany" and st.get("gov") == "nazism":
        t += "\n⚫ *رژیم نازی فعال*"
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")

# ─── ۹. هولوکاست ───
async def on_holocaust(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["country"] != "germany" or st.get("gov") != "nazism":
        await update.message.reply_text("❌ این گزینه فقط برای آلمان نازی است.")
        return
    if not pay(uid, money=3000):
        await update.message.reply_text("❌ ۳۰۰۰💰 لازمه."); return
    # اثر: اقتصاد فوق مثبت، رضایت پایین
    sset(uid,
         money=st["money"]+5000,
         steel=st["steel"]+200,
         happiness=max(0, st["happiness"]-20),
         manpower=int(st["manpower"]*0.9))
    add_effect(uid, "holocaust", 5)
    msg = (f"⚫ *هولوکاست در آلمان*\n\n"
           f"رژیم نازی برنامه پاکسازی نژادی را آغاز کرد. "
           f"یهودیان، کولی‌ها، معلولان و بیماران روانی به اردوگاه‌ها "
           f"منتقل شدند.\n\n"
           f"💰 اقتصاد: +۵۰۰۰💰\n⚙️ فولاد: +۲۰۰\n😊 رضایت: -۲۰")
    add_news(st["turn"], "holocaust", msg)
    try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
    except: pass
    await update.message.reply_text(msg, reply_markup=kb_main(), parse_mode="Markdown")

# ─── ۱۰. بمباران در ارتش ───
async def on_bomb(update, ctx):
    await update.message.reply_text("✈️ *عملیات بمباران*\nنوع بمباران 👇",
        reply_markup=kb_bomb(), parse_mode="Markdown")

# ─── ۱۱. سازمان ملل جدید - نوبتی ───
UN2 = {"active": False, "turn": 0, "order": [], "idx": 0, "phase": "idle"}

async def start_un(ctx, turn):
    """هر کشور نوبت خودش حرف می‌زنه"""
    players = all_players()
    if not players:
        return
    UN2["active"] = True
    UN2["turn"] = turn
    UN2["order"] = [p["uid"] for p in players]
    UN2["idx"] = 0
    UN2["phase"] = "speech"
    # اعلام ۵ نوبت قبل انجام شده تو auto_turn
    announce = (f"🌍 *سازمان ملل — نشست عمومی نوبت {turn}*\n\n"
                f"جلسه رسمی آغاز شد. هر کشور فرصت محدودی برای سخنرانی دارد.\n"
                f"ترتیب سخنرانی:\n")
    for i, p in enumerate(players):
        c = COUNTRIES[p["c"]]
        announce += f"{i+1}. {c['f']} {c['n']}\n"
    # زمان هر نفر
    n = len(players)
    per_min = max(1, 25 // n)  # ۲۵ دقیقه تقسیم بر تعداد
    UN2["per_min"] = per_min
    announce += f"\n⏱️ هر کشور {per_min} دقیقه فرصت دارد."
    for p in players:
        try:
            await ctx.bot.send_message(p["uid"], announce, parse_mode="Markdown")
        except: pass
    add_news(turn, "un", f"🌍 سازمان ملل — نشست عمومی نوبت {turn}")
    asyncio.create_task(un_cycle(ctx))

async def un_cycle(ctx):
    players = UN2["order"]
    per_min = UN2.get("per_min", 2)
    for i, uid in enumerate(players):
        if not UN2["active"]: return
        UN2["idx"] = i
        st = get_state(uid)
        if not st:
            continue
        c = COUNTRIES[st["country"]]
        # اعلام نوبت
        for p in all_players():
            try:
                msg = f"🎤 *نوبت {c['f']} {c['n']}*\nزمان: {per_min} دقیقه"
                if p["uid"] == uid:
                    msg += "\n\n✏️ حالا می‌تونی حرف بزنی."
                else:
                    msg += "\n\nمنتظر باش تا نوبتت برسه."
                await ctx.bot.send_message(p["uid"], msg, parse_mode="Markdown")
            except: pass
        await asyncio.sleep(per_min*60)
    UN2["active"] = False
    for p in all_players():
        try:
            await ctx.bot.send_message(p["uid"], "🌍 نشست عمومی پایان یافت.",
                reply_markup=kb_main())
        except: pass

async def on_un_message(update, ctx, text):
    if not UN2["active"]: return False
    uid = update.effective_user.id
    players = UN2["order"]
    if not players or UN2["idx"] >= len(players): return False
    current_uid = players[UN2["idx"]]
    if uid != current_uid:
        st = get_state(uid)
        if st:
            c = COUNTRIES[st["country"]]
        await update.message.reply_text(
            "⏳ نوبت تو نیست. منتظر باش تا نوبتت برسه.")
        return True
    # نوبت این کاربر - پیامش برای همه
    st = get_state(uid)
    if st:
        c = COUNTRIES[st["country"]]
        msg = f"🎤 {c['f']} {c['n']}:\n{text}"
        for p in all_players():
            try: await ctx.bot.send_message(p["uid"], msg)
            except: pass
    return True

# ─── ۱۲. process_turn با تحقیق زمان‌دار ───
_old_process_turn = process_turn

def process_turn(uid):
    st = get_state(uid)
    if not st: return None
    c = COUNTRIES[st["country"]]
    mult = 2.0 if is_vip(uid) else 1.0
    upd = {}
    tm = st["tax"] / 20.0
    upd["money"] = st["money"] + c["bm"]*tm*mult
    upd["food"] = st["food"] + c["bf"]*mult
    upd["water"] = st["water"] + c["bf"]*0.5*mult
    upd["steel"] = st["steel"] + c["bs"]*mult
    upd["oil"] = st["oil"] + c["bo"]*mult
    upd["coal"] = st["coal"] + c["bc"]*mult
    upd["manpower"] = st["manpower"] + 50*mult
    conn = db()
    bombs = conn.execute("SELECT * FROM bombing WHERE target_uid=?", (uid,)).fetchall()
    bf = 0.5 if any(b["effect"]=="factory" for b in bombs) else 1.0
    br = 0.5 if any(b["effect"]=="refinery" for b in bombs) else 1.0
    for b in bombs:
        t = b["turns"] - 1
        if t <= 0: conn.execute("DELETE FROM bombing WHERE id=?", (b["id"],))
        else: conn.execute("UPDATE bombing SET turns=? WHERE id=?", (t, b["id"]))
    conn.commit(); conn.close()
    for f in get_fact(uid):
        p = PROJECTS.get(f["fkey"])
        if p and p["eff"] in ("steel","oil","coal","food","water","money"):
            r = p["eff"]
            fac = 1.0
            if r == "oil": fac = br
            if r in ("steel","coal"): fac = bf
            upd[r] = upd.get(r, st.get(r, 0)) + p["v"]*f["level"]*mult*fac
    hap = st["happiness"] + calc_hap_delta(uid, st)
    hap = max(0, min(100, hap))
    upd["happiness"] = hap
    upd.update(check_protest(uid, st))
    if st.get("suppress_cd", 0) > 0:
        nc = st["suppress_cd"] - 1
        upd["suppress_cd"] = nc
        if nc == 0:
            upd["happiness"] = max(0, upd.get("happiness", hap) - 5)
    conn = db()
    for it in conn.execute("SELECT * FROM items WHERE turns_left>0").fetchall():
        t = it["turns_left"] - 1
        if t <= 0: conn.execute("DELETE FROM items WHERE id=?", (it["id"],))
        else: conn.execute("UPDATE items SET turns_left=? WHERE id=?", (t, it["id"]))
    conn.commit(); conn.close()
    conn = db()
    for item in get_pq(uid):
        t = item["turns"] - 1
        if t <= 0:
            # تحقیق زمان‌دار
            if item["category"] == "research_pending":
                parts = item["model"].split(":", 1)
                if len(parts) == 2:
                    mark_res(uid, parts[0], parts[1])
            else:
                add_army(uid, item["category"], item["model"], item["qty"])
            conn.execute("DELETE FROM pq WHERE id=?", (item["id"],))
        else:
            conn.execute("UPDATE pq SET turns=? WHERE id=?", (t, item["id"]))
    for p in get_projq(uid):
        t = p["turns"] - 1
        if t <= 0:
            mark_proj(uid, p["pkey"])
            conn.execute("DELETE FROM projq WHERE id=?", (p["id"],))
        else:
            conn.execute("UPDATE projq SET turns=? WHERE id=?", (t, p["id"]))
    for s in conn.execute("SELECT * FROM spies WHERE from_id=? AND status='pending'",
        (uid,)).fetchall():
        t = s["turns"] - 1
        if t <= 0:
            resolve_spy(uid, s["to_id"])
            conn.execute("UPDATE spies SET status='done' WHERE id=?", (s["id"],))
        else:
            conn.execute("UPDATE spies SET turns=? WHERE id=?", (t, s["id"]))
    conn.commit(); conn.close()
    if st.get("atomic_t", 0) > 0:
        t = st["atomic_t"] - 1
        if t <= 0:
            ns = st.get("atomic_stage", 0) + 1
            upd["atomic_stage"] = ns
            upd["atomic_t"] = 0
            if ns >= 3:
                upd["atomic_bombs"] = st.get("atomic_bombs", 0) + 1
        else:
            upd["atomic_t"] = t
    nd = next_date(st["game_date"])
    upd["game_date"] = nd
    upd["turn"] = st["turn"] + 1
    upd["last_turn"] = datetime.utcnow().isoformat()
    ev = []
    if nd in EVENTS:
        ev.append(EVENTS[nd])
        add_news(st["turn"], "hist", EVENTS[nd])
    sset(uid, **upd)
    return {"turn": st["turn"]+1, "date": nd, "ev": ev}

# ─── ۱۳. اتم مخفی قبل نوبت ۱۰۷۷ ───
async def on_atomic(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    # فقط ادمین‌ها
    if not is_admin(uid):
        if st["turn"] < ATOMIC_UNLOCK:
            await update.message.reply_text("🔒 این قابلیت هنوز باز نشده."); return
        if st["country"] not in ["germany","usa"] and gget("atomic_used") != "true":
            await update.message.reply_text("🔒 این پروژه در دسترس نیست."); return
    stage = st.get("atomic_stage", 0)
    if stage >= 3:
        await update.message.reply_text(
            f"☢️ *بمب اتمی آماده!*\nتعداد بمب: {st.get('atomic_bombs',0)}\n\n"
            f"برای استفاده: آیتم `بمب اتم` (فقط ادمین‌ها)",
            reply_markup=kb_main(), parse_mode="Markdown"); return
    s = ATOMIC_STAGES[stage]
    await update.message.reply_text(
        f"☢️ *پروژه اتمی*\nمرحله {stage}/3\n{s['n']}\n"
        f"⏱️ {s['t']} نوبت\n💰{s['m']} ⚙️{s['s']} 🛢️{s['o']}",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("☢️ شروع مرحله")],[KeyboardButton("🔙 منو")]],
            resize_keyboard=True), parse_mode="Markdown")

# ─── ۱۴. نمایش اطلاعات با آیدی ادمین ───
def render_stats(uid):
    st = get_state(uid); c = COUNTRIES[st["country"]]
    lines = [f"{c['f']} *{c['n']}* — {fmt_date(parse_date(st['game_date']))}",
        f"🔢 {st['turn']}/{TOTAL_TURNS}",
        f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}",
        f"🆔 `{uid}`",
        "━━━━━━━━━━━━━━━━",
        f"💰{fmt(st['money'])} 🍞{fmt(st['food'])} 💧{fmt(st['water'])}",
        f"⚙️{fmt(st['steel'])} 🛢️{fmt(st['oil'])} 🪨{fmt(st['coal'])}",
        f"👥{fmt(st['manpower'])} 🪖{fmt(st['soldiers'])}",
        f"😊{int(st['happiness'])}% 💵{st['tax']}% 🕵️{st.get('surveillance',20)}%"]
    for u in get_army(uid):
        lines.append(f"▪️ {u['model']}: {fmt(u['count'])}")
    return "\n".join(lines)

# ─── ۱۵. on_text نهایی ───
_old_on_text2 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text2(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    st = get_state(uid)
    # آتم مخفی
    if text == "☢️ اتم":
        await on_atomic(update, ctx); return
    # سرکوب شرطی
    if text == "🚔 سرکوب اعتراض":
        if not st or not st.get("protest"):
            await update.message.reply_text("❌ اعتراضی وجود ندارد.")
            return
        await on_suppress(update, ctx); return
    # هولوکاست
    if text == "⚫ هولوکاست":
        await on_holocaust(update, ctx); return
    # امور کشور با کیبورد جدید
    if text == "🏛️ امور کشور":
        await on_internal(update, ctx); return
    # بمباران در ارتش
    if text == "✈️ بمباران":
        if not st:
            return
        await on_bomb(update, ctx); return
    # پروژه‌ها حذف شده
    if text == "🏗️ پروژه‌ها":
        await update.message.reply_text(
            "ℹ️ پروژه‌ها حذف شده‌اند. به بخش‌های مربوطه منتقل شدند:\n"
            "🏭 صنعت/انرژی/کشاورزی → کارخونه‌ها\n"
            "🎖️ نظامی → ارتش\n"
            "🏥 اجتماعی/📜 سیاسی → امور کشور\n"
            "🛣️ حمل‌ونقل → در حال حاضر موجود نیست")
        return
    # دستورات قدیمی پروژه
    if text in ("🏭 صنعت","⚡ انرژی","🎖️ نظامی","🏥 اجتماعی",
                "🌾 کشاورزی","📜 سیاسی","🛣️ حمل‌ونقل"):
        await update.message.reply_text(
            "ℹ️ این بخش ادغام شده. از کارخونه‌ها یا ارتش استفاده کن.")
        return
    # سخنرانی حذف شده
    if text == "📢 سخنرانی":
        await update.message.reply_text("ℹ️ سخنرانی حذف شد. خودکار انجام می‌شود.")
        return
    # UN چک
    if await on_un_message(update, ctx, text): return
    return await _old_on_text2(update, ctx)

# ─── ۱۶. auto_turn جدید با هشدار UN ───
_old_auto_turn = auto_turn

async def auto_turn(ctx):
    if gget("season_ended") == "true": return
    nt = int(gget("turn","1")) + 1
    # هشدار ۵ نوبت قبل UN
    if nt % UN_INTERVAL == 5 and nt > 0:
        next_un = nt + 5
        for p in all_players():
            try:
                await ctx.bot.send_message(p["uid"],
                    f"🌍 *اطلاعیه*\n\n۵ نوبت دیگر (نوبت {next_un}) "
                    f"نشست عمومی سازمان ملل برگزار می‌شود. آماده باش.")
            except: pass
    # اجرای auto_turn قدیمی
    await _old_auto_turn(ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ نهایی — همه قابلیت‌ها کامل
# ═══════════════════════════════════════════════════════════════

TARGET_FREE_ITEMS = ("carpet_bomb", "war_speech", "war_storm", "revive",
                     "god_shield", "invisible", "double_attack", "lock_on",
                     "revenge", "seize_power")

def add_news_send(turn, cat, text):
    """افزودن خبر + ارسال فوری به کانال"""
    add_news(turn, cat, text)
    return text

# ─── پچ ۱: صلح واقعی + قبول/رد کامل ───
async def on_neg_resp(update, ctx, nid, acc):
    uid = update.effective_user.id
    conn = db()
    r = conn.execute("SELECT * FROM negs WHERE id=? AND to_id=?", (nid, uid)).fetchone()
    if not r:
        conn.close(); await update.message.reply_text("❌ درخواست پیدا نشد."); return
    r = dict(r)
    conn.execute("UPDATE negs SET status=? WHERE id=?",
        ("accepted" if acc else "rejected", nid))
    if acc and r["kind"] == "nap":
        add_nap(uid, r["from_id"], int(gget("turn","1"))+10)
    if acc and r["kind"] == "cancel_nap":
        cancel_nap(uid, r["from_id"])
    if acc and r["kind"] == "alliance":
        try:
            aid = int(r["payload"])
            conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
        except: pass
    if acc and r["kind"] == "peace":
        from_uid = r["from_id"]; to_uid = uid
        conn.execute("DELETE FROM wars WHERE (atk_uid=? AND def_uid=?) OR (atk_uid=? AND def_uid=?)",
            (from_uid, to_uid, to_uid, from_uid))
        conn.execute("UPDATE states SET war=0 WHERE user_id=?", (from_uid,))
        conn.execute("UPDATE states SET war=0 WHERE user_id=?", (to_uid,))
        conn.execute("UPDATE states SET war=0 WHERE user_id=?", (from_uid,))
        # همه wars مربوطه رو حذف کن
        conn.execute("DELETE FROM wars WHERE atk_uid=? OR def_uid=?", (from_uid, from_uid))
        conn.execute("DELETE FROM wars WHERE atk_uid=? OR def_uid=?", (to_uid, to_uid))
        # برگردوندن war=0
        for u in all_players():
            conn.execute("UPDATE states SET war=0 WHERE user_id=?", (u["uid"],))
        fs = get_state(from_uid); ts = get_state(to_uid)
        if fs and ts:
            peace_msg = (f"☮️ *صلح میان {COUNTRIES[fs['country']]['n']} و "
                         f"{COUNTRIES[ts['country']]['n']}*\n\n"
                         f"پس از مذاکرات فشرده، دو کشور رسماً به مخاصمات "
                         f"پایان دادند و توافق صلح امضا شد.")
            add_news(int(gget("turn","1")), "peace", peace_msg)
            try: await ctx.bot.send_message(NEWS_CH, peace_msg, parse_mode="Markdown")
            except: pass
            try: await ctx.bot.send_message(from_uid, peace_msg, parse_mode="Markdown")
            except: pass
    conn.commit(); conn.close()
    msg = "✅ قبول" if acc else "❌ رد"
    await update.message.reply_text(f"درخواست: {msg}", reply_markup=kb_main())
    try: await ctx.bot.send_message(r["from_id"], f"📩 پاسخ درخواستت: {msg}")
    except: pass

# ─── پچ ۲: آیتم‌ها کامل با اثر واقعی ───
async def apply_item_effect(ctx, uid, item_key, target_uid=None):
    st = get_state(uid)
    if not st: return "❌ خطا"
    c = COUNTRIES[st["country"]]
    result = "✅"
    # آیتم‌های بدون هدف
    if item_key in TARGET_FREE_ITEMS:
        if item_key == "carpet_bomb":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps:
                    sset(p["uid"], happiness=max(0, ps["happiness"]-10),
                         soldiers=int(ps["soldiers"]*0.9))
            result = "🔥 بمباران قالی — همه دشمنان آسیب دیدند."
        elif item_key == "war_speech":
            total = 0
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps:
                    half = ps["money"]*0.5
                    total += half
                    sset(p["uid"], money=max(0, ps["money"]-half))
            sset(uid, money=st["money"]+total)
            result = f"📢 نطق جنگی — {fmt(total)} پول جمع شد."
        elif item_key == "war_storm":
            # همه جنگ‌های فعال علیه کاربر لغو می‌شن
            conn = db()
            conn.execute("DELETE FROM wars WHERE def_uid=?", (uid,))
            conn.commit(); conn.close()
            sset(uid, war=0)
            result = "🌪 طوفان جنگی — همه حملات دشمن متوقف شد."
        elif item_key == "revive":
            add_effect(uid, "revive", 999)
            result = "🔄 محافظت مرگ فعال شد (تا استفاده)."
        elif item_key == "god_shield":
            add_effect(uid, "shield", 60)
            result = "🛡 سپر جان — ۱ ساعت نامیرا."
        elif item_key == "invisible":
            add_effect(uid, "invisible", 30)
            result = "👻 نامرئی — ۳۰ دقیقه."
        elif item_key == "double_attack":
            add_effect(uid, "double_attack", 10)
            result = "⚡ دوبرابر حمله — ۱۰ نوبت."
        elif item_key == "lock_on":
            add_effect(uid, "lock_on", 10)
            result = "🎯 قفل روی حریف — ۱۰ نوبت."
        elif item_key == "revenge":
            add_effect(uid, "revenge", 999)
            result = "💀 انتقام فعال شد (تاحذف)."
        elif item_key == "seize_power":
            add_effect(uid, "commander", 10)
            # اثر: ۲۰٪ از تولید همه بازیکنان به این کاربر
            result = f"👑 {c['n']} ۱۰ نوبت فرمانده کل شد."
        add_news(st["turn"], "item", result)
        return result
    # آیتم‌های هدف‌دار
    if item_key == "force_exile" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"🗳 {COUNTRIES[ts['country']]['n']} از بازی اخراج شد."
    elif item_key == "censor" and target_uid:
        add_effect(target_uid, "censored", 3)
        result = f"🤐 {COUNTRIES[get_state(target_uid)['country']]['n']} ۳ نوبت سانسور شد."
    elif item_key == "expose" and target_uid:
        ts = get_state(target_uid)
        if ts:
            info = render_stats(target_uid)
            try:
                await ctx.bot.send_message(uid,
                    f"🕵️ *اطلاعات فاش‌شده {COUNTRIES[ts['country']]['n']}*\n\n{info}",
                    parse_mode="Markdown")
            except: pass
            result = f"🕵️ اطلاعات {COUNTRIES[ts['country']]['n']} برای تو ارسال شد."
    elif item_key == "force_ally" and target_uid:
        aid = get_user_alliance(uid)
        if not aid:
            conn = db()
            cur = conn.execute("INSERT INTO alliances(name,founder) VALUES(?,?)",
                (f"اتحاد {c['n']}", uid))
            aid = cur.lastrowid
            conn.execute("INSERT INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
            conn.commit(); conn.close()
        conn = db()
        conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, target_uid))
        conn.commit(); conn.close()
        result = f"🤝 {COUNTRIES[get_state(target_uid)['country']]['n']} به اتحاد اضافه شد."
    elif item_key == "plunder" and target_uid:
        ts = get_state(target_uid)
        if ts:
            money_half = ts["money"] // 2
            steel_half = ts["steel"] // 2
            oil_half = ts["oil"] // 2
            sset(target_uid, money=ts["money"]-money_half,
                 steel=ts["steel"]-steel_half, oil=ts["oil"]-oil_half)
            sset(uid, money=st["money"]+money_half,
                 steel=st["steel"]+steel_half, oil=st["oil"]+oil_half)
            result = f"💰 غارت — {fmt(money_half)}💰 + {fmt(steel_half)}⚙️ + {fmt(oil_half)}🛢️"
    elif item_key == "tsar_bomb" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"💣 بمب تزار — {COUNTRIES[ts['country']]['n']} نابود شد."
            # ارسال به کانال
            try:
                await ctx.bot.send_message(NEWS_CH,
                    f"💣 *بمب تزار*\n\n{COUNTRIES[st['country']]['n']} "
                    f"بمب تزار را بر فراز پایتخت {COUNTRIES[ts['country']]['n']} "
                    f"منفجر کرد. شهر کاملاً نابود شد.",
                    parse_mode="Markdown")
            except: pass
    elif item_key == "nuke_item" and target_uid:
        result = use_atomic(uid, target_uid)
        try:
            ts = get_state(target_uid)
            if ts:
                await ctx.bot.send_message(NEWS_CH,
                    f"☢️ *بمب اتم*\n\nاولین بمب اتمی تاریخ توسط "
                    f"{COUNTRIES[st['country']]['n']} بر فراز پایتخت "
                    f"{COUNTRIES[ts['country']]['n']} منفجر شد.",
                    parse_mode="Markdown")
        except: pass
    elif item_key == "bio_weapon" and target_uid:
        add_effect(target_uid, "no_attack", 5)
        result = f"☠️ {COUNTRIES[get_state(target_uid)['country']]['n']} ۵ نوبت نمی‌تونه حمله کنه."
    elif item_key == "ballistic" and target_uid:
        ts = get_state(target_uid)
        if ts:
            sset(target_uid, dead=1)
            result = f"🚀 موشک بالستیک — {COUNTRIES[ts['country']]['n']} از بازی حذف شد."
    add_news(st["turn"], "item", result)
    return result

# ─── پچ ۳: جنگ با هشدار اتحاد ───
def advance_wars():
    conn = db()
    wars = conn.execute("SELECT * FROM wars").fetchall()
    conn.close()
    for w in wars:
        au = w["atk_uid"]; du = w["def_uid"]
        ast = get_state(au); dst = get_state(du)
        if not ast or not dst or dst.get("dead"):
            conn = db()
            conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
            conn.commit(); conn.close()
            continue
        t = w["turns"] - 1
        stage = w["stage"]
        if stage == "move" and t <= 0:
            my = calc_power(au, "attack")
            en = calc_power(du, "defense")
            # اتحاد اجباری - مدافع
            aid_d = get_user_alliance(du)
            if aid_d:
                for m in get_alliance_members(aid_d):
                    if m != du and m != au:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            en += calc_power(m, "defense")
                            add_news(int(gget("turn","1")), f"ally_war_{m}",
                                f"⚠️ {COUNTRIES[w['attacker']]['n']} به متحدت "
                                f"{COUNTRIES[w['defender']]['n']} حمله کرد. "
                                f"بر اساس پیمان، تو هم وارد جنگ شدی.")
            # اتحاد اجباری - حمله‌کننده
            aid_a = get_user_alliance(au)
            if aid_a:
                for m in get_alliance_members(aid_a):
                    if m != au and m != du:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            my += calc_power(m, "attack")
                            add_news(int(gget("turn","1")), f"ally_war_{m}",
                                f"⚠️ متحدت {COUNTRIES[w['attacker']]['n']} به "
                                f"{COUNTRIES[w['defender']]['n']} حمله کرد. "
                                f"بر اساس پیمان، تو هم وارد جنگ شدی.")
            # اثر revive/shield
            if has_effect(du, "shield"):
                my = int(my * 0.1)
            battle_msg = (f"⚔️ *نبرد {COUNTRIES[w['attacker']]['n']} و "
                          f"{COUNTRIES[w['defender']]['n']}*\n\n"
                          f"قدرت حمله: {fmt(my)}\nقدرت دفاع: {fmt(en)}")
            add_news(int(gget("turn","1")), "battle", battle_msg)
            try:
                # ارسال به کانال از طریق وظیفه بعدی
                pass
            except: pass
            if my > en:
                loss_pct = max(0.10, min(0.30, 0.15 * (1 + (my-en)/max(1,my))))
                for u in get_army(au):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (max(0, int(u["count"]*(1-loss_pct))), u["id"]))
                    conn.commit(); conn.close()
                ds = get_state(du)
                if ds:
                    sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5,
                         oil=ds["oil"]*0.5, soldiers=int(ds["soldiers"]*0.5))
                conn = db()
                conn.execute("UPDATE wars SET stage='resolve', turns=1 WHERE id=?",
                    (w["id"],))
                conn.commit(); conn.close()
                add_news(int(gget("turn","1")), "war",
                    f"🏆 {COUNTRIES[w['attacker']]['n']} در نبرد اولیه پیروز شد.")
                # اگه طرف مقابل خیلی ضعیف شد → فتح
                if calc_power(du, "defense") < my * 0.2:
                    conquer_country(None, au, du)
            else:
                loss_pct = random.uniform(0.30, 0.50)
                for u in get_army(au):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (max(0, int(u["count"]*(1-loss_pct))), u["id"]))
                    conn.commit(); conn.close()
                conn = db()
                conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
                conn.commit(); conn.close()
                add_news(int(gget("turn","1")), "war",
                    f"💀 حمله {COUNTRIES[w['attacker']]['n']} شکست خورد.")
        elif stage == "resolve":
            ds = get_state(du)
            if ds:
                sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5)
                for u in get_army(du):
                    conn = db()
                    conn.execute("UPDATE army SET count=? WHERE id=?",
                        (int(u["count"]*0.5), u["id"]))
                    conn.commit(); conn.close()
                conquer_country(None, au, du)
            conn = db()
            conn.execute("DELETE FROM wars WHERE id=?", (w["id"],))
            conn.commit(); conn.close()

# ─── پچ ۴: تحویل پیام‌های هشدار ───
async def deliver_pending(ctx):
    for p in all_players():
        uid = p["uid"]
        key = f"msg_read_{uid}"
        last_read = int(gget(key, "0") or 0)
        conn = db()
        rows = conn.execute(
            "SELECT * FROM news WHERE id>? AND (cat=? OR cat=? OR cat=? OR cat=? OR cat=?) ORDER BY id",
            (last_read, f"spy_ok_{uid}", f"spy_fail_{uid}",
             f"spy_caught_{uid}", f"ally_war_{uid}", f"conquest_{uid}")).fetchall()
        conn.close()
        for r in rows:
            try:
                if r["cat"].startswith("spy_ok_"):
                    await ctx.bot.send_message(uid,
                        f"✅ *جاسوسی موفق!*\n━━━━━━━━━━━━━━━━\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_fail_"):
                    await ctx.bot.send_message(uid,
                        f"❌ *جاسوس لو رفت!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_caught_"):
                    await ctx.bot.send_message(uid,
                        f"🚨 *هشدار امنیتی!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("ally_war_"):
                    await ctx.bot.send_message(uid,
                        f"⚠️ *هشدار اتحاد!*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                elif r["cat"].startswith("conquest_"):
                    await ctx.bot.send_message(uid,
                        f"💀 *اطلاعیه*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                last_read = r["id"]
            except: pass
        gset(key, str(last_read))

# ─── پچ ۵: on_text wrapper برای آیتم‌های بدون هدف ───
_old_on_text = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text in ITEM_FA and is_admin(uid):
        ik = ITEM_FA[text]
        if ik in TARGET_FREE_ITEMS:
            result = await apply_item_effect(ctx, uid, ik)
            await update.message.reply_text(result, reply_markup=kb_main())
            return
    return await _old_on_text(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — همه اخبار هر نوبت، قاطی هم
# ═══════════════════════════════════════════════════════════════

async def news_post(ctx, title, body=""):
    if body:
        text = f"📰 *{title}*\n━━━━━━━━━━━━━━━━\n{body}"
    else:
        text = f"📰 *{title}*"
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"news ch: {e}")

_old_auto_turn_all = auto_turn

async def auto_turn(ctx):
    if gget("season_ended") == "true": return
    # ۱. جنگ‌ها
    advance_wars()
    # ۲. همه بازیکن‌ها
    players = all_players()
    nt = int(gget("turn","1")) + 1
    gset("turn", nt)
    # لیست همه خبرها
    news_items = []
    for p in players:
        try:
            res = process_turn(p["uid"])
            if not res: continue
            if res["ev"]:
                for e in res["ev"]:
                    news_items.append(("hist", e))
            t = f"📅 *نوبت {nt}* — {fmt_date(parse_date(res['date']))}\n"
            if res["ev"]:
                for e in res["ev"]:
                    t += f"• {e}\n"
            await ctx.bot.send_message(p["uid"], t,
                parse_mode="Markdown", reply_markup=kb_main())
        except Exception as e:
            log.warning(f"turn {p['uid']}: {e}")
    # ۳. خبرهای عمومی این نوبت
    conn = db()
    public_cats = ("war","battle","conquest","protest","suppress",
                   "un","statement","item","holocaust","peace",
                   "conscription","bomb")
    rows = conn.execute(
        f"SELECT * FROM news WHERE turn>=? AND cat IN ({','.join('?'*len(public_cats))}) ORDER BY id",
        (nt-2, *public_cats)).fetchall()
    conn.close()
    seen = set()
    for r in rows:
        key = r["text"][:50]
        if key in seen: continue
        seen.add(key)
        news_items.append((r["cat"], r["text"]))
    # ۴. خبر سرگرمی — هر نوبت
    news_items.append(("fun", random.choice(RANDOM_NEWS).format(n=random.randint(10, 500))))
    # ۵. ارسال همه به کانال تو یه پست
    if news_items:
        # تاریخ فعلی
        try:
            any_st = get_state(players[0]["uid"]) if players else None
            date_str = fmt_date(parse_date(any_st["game_date"])) if any_st else "—"
        except: date_str = "—"
        lines = [
            f"📰 *WORLD WAR NEWS — نوبت {nt}*",
            f"🗓️ {date_str}",
            "━━━━━━━━━━━━━━━━",
        ]
        cat_emoji = {
            "hist":"📜","war":"⚔️","battle":"🎯","conquest":"🏆",
            "protest":"🔥","suppress":"🚔","un":"🌍","statement":"📢",
            "item":"🎁","holocaust":"⚫","peace":"☮️",
            "conscription":"📋","bomb":"✈️","fun":"🎭",
        }
        for cat, txt in news_items:
            em = cat_emoji.get(cat, "•")
            lines.append(f"{em} {txt}")
        full = "\n".join(lines)
        # چک طول پیام
        if len(full) > 4000:
            full = full[:3900] + "\n...(ادامه در کانال)"
        try:
            await ctx.bot.send_message(NEWS_CH, full, parse_mode="Markdown")
        except Exception as e:
            log.warning(f"news: {e}")
    # ۶. اتم باز شد
    if nt == ATOMIC_UNLOCK:
        try:
            await ctx.bot.send_message(NEWS_CH,
                "☢️ *پروژه اتمی*\n\nپروژه منهتن امروز رسماً آغاز شد.",
                parse_mode="Markdown")
        except: pass
    # ۷. هشدار UN
    if nt % UN_INTERVAL == 5 and nt > 0:
        next_un = nt + 5
        for p in all_players():
            try:
                await ctx.bot.send_message(p["uid"],
                    f"🌍 *اطلاعیه*\n\n۵ نوبت دیگر (نوبت {next_un}) "
                    f"نشست عمومی سازمان ملل برگزار می‌شود.")
            except: pass
    # ۸. سازمان ملل
    if nt % UN_INTERVAL == 0 and nt > 0:
        try:
            if 'start_un' in globals():
                await start_un(ctx, nt)
        except Exception as e: log.warning(f"UN: {e}")
    # ۹. جاسوسی معلق
    try: await deliver_pending(ctx)
    except Exception as e: log.warning(f"deliver: {e}")
    # ۱۰. پایان سیزن
    if nt >= TOTAL_TURNS:
        gset("season_ended", "true")
        for p in players:
            try:
                await ctx.bot.send_message(p["uid"],
                    "🏁 *سیزن به پایان رسید!*\n\nبرای شروع جدید /start بزن.",
                    parse_mode="Markdown")
            except: pass

async def post_to_channel(ctx, text):
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"post_to_channel: {e}")# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — فیکس زنجیره تحقیقات
# ═══════════════════════════════════════════════════════════════

# مدل اول (index 0) همیشه باز — چک زنجیره فقط از index 1
def research_chain_ok(uid, cat, idx, tree, researched):
    """اگه idx == 0 → همه چی اوکیه (مدل اول از اول بازه)"""
    if idx <= 0:
        return True, None
    # از index 1 چک کن تا idx-1
    for j in range(1, idx):
        if tree[j][0] not in researched:
            return False, tree[j][0]
    return True, None

async def on_research_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"research_{cat}"
    lines = [f"🔬 *{CAT_N[cat]}*","━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power, cost, build, steel, oil, desc = item
        if i == 0:
            lines.append(f"✅ *{name}* (از اول باز)")
            continue
        if name in researched:
            lines.append(f"✅ *{name}* — قدرت {power}")
            continue
        # چک زنجیره (فقط از index 1)
        ok, need = research_chain_ok(uid, cat, i, tree, researched)
        if not ok:
            lines.append(f"🔒 *{name}* (ابتدا {need} را تحقیق کن)")
        else:
            lines.append(
                f"🔓 *{name}*\n"
                f"   📝 {desc}\n"
                f"   💪 {power} | 🔬 {cost}💰+{build}نوبت | ⚙️{steel} 🛢️{oil}"
            )
    lines.append("\n👇 روی مدل بزن")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

# ─── hook روتر برای پیک تحقیقات ───
_old_on_text13 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text13(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    st = get_state(uid)
    if not st:
        return await _old_on_text13(update, ctx)
    screen = ctx.user_data.get("screen", "menu")
    if screen.startswith("research_"):
        cat = screen.split("_", 1)[1]
        tree = get_tree(st["country"], cat)
        researched = get_res(uid, cat)
        for i, item in enumerate(tree):
            if len(item) < 7: continue
            name, power, cost, build, steel, oil, desc = item
            if name == text:
                if i == 0:
                    await update.message.reply_text("این مدل از اول باز است.")
                    return
                if name in researched:
                    await update.message.reply_text("قبلاً تحقیق شده.")
                    return
                # چک زنجیره (فقط از index 1)
                ok, need = research_chain_ok(uid, cat, i, tree, researched)
                if not ok:
                    await update.message.reply_text(
                        f"🔒 ابتدا باید *{need}* را تحقیق کنی.",
                        parse_mode="Markdown")
                    return
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰")
                    return
                conn = db()
                conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
                    (uid, "research_pending", f"{cat}:{name}", 1, build))
                conn.commit(); conn.close()
                await update.message.reply_text(
                    f"🔬 *{name}* در صف تحقیق!\n⏱️ {build} نوبت\n💰 {cost}",
                    reply_markup=kb_main(), parse_mode="Markdown")
                return
    return await _old_on_text13(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — محدودیت اقدامات امور کشور
# ═══════════════════════════════════════════════════════════════

# هر اقدام: (هزینه، رضایت، کول‌داون نوبت، توضیح)
INTERNAL_ACTIONS = {
    "🏥 بیمارستان جدید": (500, 5, 3, "بیمارستان مدرن افتتاح شد."),
    "📚 مدرسه جدید": (400, 4, 3, "مدارس جدید ساخته شدند."),
    "💧 سیستم آب": (600, 6, 4, "آب سالم به همه رسید."),
    "🏠 مسکن": (700, 7, 4, "پروژه مسکن عمومی آغاز شد."),
    "🍞 سهمیه غذا": (400, 5, 2, "سهمیه غذایی توزیع شد."),
    "📜 اصلاحات مدنی": (600, 6, 5, "قوانین مدنی اصلاح شد."),
    "⚖️ قضایی": (500, 5, 5, "سیستم قضایی تقویت شد."),
    "💰 مبارزه با فساد": (800, 8, 6, "فساد اداری سرکوب شد."),
    "📻 تبلیغات": (500, 5, 3, "رسانه‌ها در خدمت دولت."),
    "💼 برنامه اشتغال": (900, 9, 5, "فرصت‌های شغلی جدید."),
    "🏗️ زیرساخت": (800, 7, 4, "پروژه‌های زیربنایی آغاز شد."),
    "🚨 مبارزه با جرم": (700, 6, 4, "نیروهای پلیس تقویت شدند."),
    "🏭 بیکاری": (900, 8, 5, "کارخانه‌های جدید افتتاح."),
    "🚧 اعتراضات": (500, 5, 3, "کانال‌های گفتگو با معترضان."),
    "💰 کاهش مالیات": (0, 3, 8, "مالیات کمی کاهش یافت."),
    "📉 کنترل قیمت‌ها": (600, 6, 5, "قیمت‌ها کنترل شد."),
}

def can_do_action(uid, action):
    """چک کن می‌تونه این اقدام رو بکنه؟"""
    st = get_state(uid)
    if not st: return False, "❌ خطا"
    info = INTERNAL_ACTIONS.get(action)
    if not info: return False, "❌ اقدام نامعتبر"
    cost, sat, cd, desc = info
    # کول‌داون
    key = f"action_{action.replace(' ','_')}_{uid}"
    last = int(gget(key, "0") or 0)
    if last > 0:
        turns_since = st["turn"] - last
        if turns_since < cd:
            rem = cd - turns_since
            return False, f"⏳ این اقدام {rem} نوبت دیگر قابل استفاده است."
    # اگه پرداخت نمی‌تونه
    if not is_admin(uid):
        if st["money"] < cost:
            return False, f"❌ نیاز: {cost}💰"
    # حد روزانه — حداکثر ۱ اقدام در هر نوبت
    last_any = int(gget(f"last_action_any_{uid}", "0") or 0)
    if last_any == st["turn"]:
        return False, "⚠️ در این نوبت یک اقدام انجام دادی. نوبت بعد دوباره."
    return True, (cost, sat, desc)

async def on_int_action(update, ctx, action):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    ok, data = can_do_action(uid, action)
    if not ok:
        await update.message.reply_text(data)
        return
    cost, sat, desc = data
    if cost > 0:
        if not pay(uid, money=cost):
            await update.message.reply_text(f"❌ نیاز: {cost}💰")
            return
    st2 = get_state(uid)
    sset(uid, happiness=min(100, st2["happiness"]+sat))
    gset(f"action_{action.replace(' ','_')}_{uid}", str(st["turn"]))
    gset(f"last_action_any_{uid}", str(st["turn"]))
    gset(f"last_int_{uid}", str(st["turn"]))
    cd = INTERNAL_ACTIONS[action][2]
    await update.message.reply_text(
        f"✅ *{action}*\n\n{desc}\n\n"
        f"😊 رضایت: +{sat}\n"
        f"💰 هزینه: {cost}\n"
        f"⏳ کول‌داون: {cd} نوبت",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── hook روتر ───
_old_on_text11 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text11(update, ctx)
    text = update.message.text.strip()
    if text in INTERNAL_ACTIONS:
        await on_int_action(update, ctx, text); return
    return await _old_on_text11(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ — هولوکاست + نازیسم
# ═══════════════════════════════════════════════════════════════

# ─── نام داینامیک کشور ───
def country_name(uid):
    st = get_state(uid)
    if not st: return "?"
    c = COUNTRIES[st["country"]]
    if st["country"] == "germany" and st.get("gov") == "nazism":
        return "آلمان نازی"
    return c["n"]

# ─── کیبورد حکومت با نازیسم ───
def kb_gov():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👑 پادشاهی مطلقه"),KeyboardButton("👑 پادشاهی مشروطه")],
        [KeyboardButton("🗳️ جمهوری ریاستی"),KeyboardButton("🗳️ جمهوری پارلمانی")],
        [KeyboardButton("🚩 فاشیسم"),KeyboardButton("⚫ نازیسم")],
        [KeyboardButton("🚩 کمونیسم"),KeyboardButton("🚩 تک‌حزبی")],
        [KeyboardButton("⚙️ دیکتاتوری نظامی"),KeyboardButton("⚙️ دیکتاتوری شخصی")],
        [KeyboardButton("🕊️ دموکراسی لیبرال"),KeyboardButton("🕊️ دموکراسی اجتماعی")],
        [KeyboardButton("⚖️ تئوکراسی")]],
        resize_keyboard=True, one_time_keyboard=True)

async def on_gov_pick(update, ctx):
    if ctx.user_data.get("wait") != "gov": return
    text = update.message.text.strip()
    gmap = {
        "👑 پادشاهی مطلقه":"absolute_monarchy",
        "👑 پادشاهی مشروطه":"constitutional_monarchy",
        "🗳️ جمهوری ریاستی":"presidential_republic",
        "🗳️ جمهوری پارلمانی":"parliamentary_republic",
        "🚩 فاشیسم":"fascist",
        "⚫ نازیسم":"nazism",
        "🚩 کمونیسم":"communism",
        "🚩 تک‌حزبی":"single_party",
        "⚙️ دیکتاتوری نظامی":"military_dictatorship",
        "⚙️ دیکتاتوری شخصی":"personal_dictatorship",
        "🕊️ دموکراسی لیبرال":"liberal_democracy",
        "🕊️ دموکراسی اجتماعی":"social_democracy",
        "⚖️ تئوکراسی":"theocracy",
    }
    if text not in gmap: return
    uid = update.effective_user.id
    pset(uid, gov=gmap[text])
    ctx.user_data["wait"] = None
    st = get_state(uid)
    await update.message.reply_text(f"✅\n\n{render_dash(st)}",
        reply_markup=kb_main(), parse_mode="Markdown")

# ─── render_dash با نام داینامیک ───
def render_dash(st):
    c = COUNTRIES[st["country"]]
    name = "آلمان نازی" if (st["country"] == "germany" and
                              st.get("gov") == "nazism") else c["n"]
    return (f"{c['f']} *{name}* — {fmt_date(parse_date(st['game_date']))}\n"
            f"🔢 نوبت: {st['turn']} / {TOTAL_TURNS}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 {fmt(st['money'])}  🍞 {fmt(st['food'])}  ⚙️ {fmt(st['steel'])}\n"
            f"🛢️ {fmt(st['oil'])}  🪨 {fmt(st['coal'])}  👥 {fmt(st['manpower'])}\n"
            f"🪖 سرباز: {fmt(st['soldiers'])}\n"
            f"😊 {int(st['happiness'])}%  💵 {st['tax']}%")

# ─── render_stats با نام داینامیک ───
def render_stats(uid):
    st = get_state(uid); c = COUNTRIES[st["country"]]
    name = "آلمان نازی" if (st["country"] == "germany" and
                              st.get("gov") == "nazism") else c["n"]
    lines = [
        f"{c['f']} *{name}* — {fmt_date(parse_date(st['game_date']))}",
        f"🔢 نوبت {st['turn']}/{TOTAL_TURNS}",
        f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}",
        f"🆔 `{uid}`",
        "━━━━━━━━━━━━━━━━",
        f"💰{fmt(st['money'])} 🍞{fmt(st['food'])} 💧{fmt(st['water'])}",
        f"⚙️{fmt(st['steel'])} 🛢️{fmt(st['oil'])} 🪨{fmt(st['coal'])}",
        f"👥{fmt(st['manpower'])} 🪖{fmt(st['soldiers'])}",
        f"😊{int(st['happiness'])}% 💵{st['tax']}% 🕵️{st.get('surveillance',20)}%",
    ]
    for u in get_army(uid):
        lines.append(f"▪️ {u['model']}: {fmt(u['count'])}")
    aid = get_user_alliance(uid)
    if aid:
        members = [m for m in get_alliance_members(aid) if m != uid]
        names = []
        for m in members:
            ms = get_state(m)
            if ms: names.append(country_name(m))
        if names:
            lines.append(f"🤝 متحدین: {', '.join(names)}")
    conn = db()
    naps = conn.execute("SELECT * FROM nap WHERE a=? OR b=?", (uid, uid)).fetchall()
    conn.close()
    for n in naps:
        other = n["b"] if n["a"] == uid else n["a"]
        lines.append(f"🤐 NAP با {country_name(other)} تا نوبت {n['until_turn']}")
    conn = db()
    wars = conn.execute("SELECT * FROM wars WHERE atk_uid=? OR def_uid=?", (uid, uid)).fetchall()
    conn.close()
    for w in wars:
        if w["atk_uid"] == uid:
            lines.append(f"⚔️ حمله به {country_name(w['def_uid'])}")
        else:
            lines.append(f"🛡 دفاع از حمله {country_name(w['atk_uid'])}")
    return "\n".join(lines)

# ─── کیبورد امور کشور ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب اعتراض")])
    rows.append([KeyboardButton("🕵️ نظارت بر مردم")])
    if st and st["country"] == "germany" and st.get("gov") == "nazism":
        rows.append([KeyboardButton("⚫ هولوکاست")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    t = (f"🏛️ *امور کشور {country_name(uid)}*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n"
         f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}\n")
    if st.get("protest"):
        t += f"\n🔥 *اعتراض فعال* ({st.get('protest_t',0)} نوبت مانده)"
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")

# ─── هولوکاست ───
async def on_holocaust(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if st["country"] != "germany" or st.get("gov") != "nazism":
        await update.message.reply_text("❌ در دسترس نیست.")
        return
    if not pay(uid, money=3000):
        await update.message.reply_text("❌ ۳۰۰۰💰 لازمه.")
        return
    sset(uid,
         money=st["money"]+5000,
         steel=st["steel"]+200,
         happiness=max(0, st["happiness"]-20),
         manpower=int(st["manpower"]*0.9))
    add_effect(uid, "holocaust", 5)
    msg = (f"⚫ *هولوکاست*\n\n"
           f"رژیم نازی برنامه‌ای گسترده علیه یهودیان، کولی‌ها، معلولان و "
           f"بیماران روانی آغاز کرد. میلیون‌ها انسان به اردوگاه‌های کار "
           f"اجباری و اتاق‌های گاز فرستاده شدند.\n\n"
           f"📈 اقتصاد: +۵۰۰۰💰\n"
           f"📈 فولاد: +۲۰۰⚙️\n"
           f"📉 رضایت: -۲۰")
    add_news(st["turn"], "holocaust", msg)
    try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
    except: pass
    await update.message.reply_text(msg, reply_markup=kb_main(), parse_mode="Markdown")

# ─── hook روتر ───
_old_on_text6 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text6(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "⚫ هولوکاست":
        await on_holocaust(update, ctx); return
    if text == "🏛️ امور کشور":
        await on_internal(update, ctx); return
    return await _old_on_text6(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ کامل — همه تغییرات جدید
# ═══════════════════════════════════════════════════════════════

# ─── ۱. کیبورد اصلی: حذف اقتصاد ───
def kb_main():
    return ReplyKeyboardMarkup([
        [KeyboardButton("⚔️ ارتش"),KeyboardButton("🔬 تحقیقات")],
        [KeyboardButton("🏭 کارخونه‌ها"),KeyboardButton("🤝 دیپلماسی")],
        [KeyboardButton("📦 تجارت"),KeyboardButton("🎯 حمله")],
        [KeyboardButton("🕵️ جاسوسی"),KeyboardButton("💵 مالیات")],
        [KeyboardButton("🏛️ امور کشور"),KeyboardButton("📊 آمار کامل")],
    ],resize_keyboard=True)

# ─── ۲. مالیات ۱-۱۰۰ ───
async def on_tax(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    ctx.user_data["wait"] = "tax"
    c = COUNTRIES[st["country"]]
    cur = int(c["bm"] * (st["tax"]/20))
    await update.message.reply_text(
        f"💵 *مالیات*\n\n"
        f"📊 فعلی: {st['tax']}%\n"
        f"📈 درآمد در نوبت: +{fmt(cur)}\n"
        f"😊 رضایت: {int(st['happiness'])}%\n\n"
        f"عددی از ۱ تا ۱۰۰ بفرست.\n"
        f"هرچه بیشتر → پول بیشتر، رضایت کمتر، خطر اعتراض بالاتر.",
        reply_markup=kb_back(), parse_mode="Markdown")

async def on_tax_input(update, ctx):
    if ctx.user_data.get("wait") != "tax": return False
    text = update.message.text.strip().replace("%","").strip()
    try:
        v = int(text)
        if not (1 <= v <= 100): raise ValueError
    except:
        await update.message.reply_text("❌ فرمت نامعتبر. عدد ۱ تا ۱۰۰ بفرست.")
        return True
    uid = update.effective_user.id
    st = get_state(uid)
    sset(uid, tax=v)
    c = COUNTRIES[st["country"]]
    new_income = int(c["bm"] * (v/20))
    ctx.user_data["wait"] = None
    st2 = get_state(uid)
    warn = ""
    if v >= 70:
        warn = "\n⚠️ مالیات بسیار بالا! خطر اعتراض جدی."
    elif v >= 50:
        warn = "\n⚠️ مالیات بالا — نارضایتی در راه."
    await update.message.reply_text(
        f"✅ مالیات: {v}%\n"
        f"📈 درآمد در نوبت: +{fmt(new_income)}{warn}\n\n"
        f"{render_dash(st2)}",
        reply_markup=kb_main(), parse_mode="Markdown")
    return True

# ─── ۳. تحقیقات: گیت زنجیره‌ای ───
def research_chain_ok(uid, cat, idx, tree, researched):
    """فقط اگه همه قبلی‌ها تحقیق شده باشن"""
    for j in range(idx):
        if tree[j][0] not in researched:
            return False, tree[j][0]
    return True, None

async def on_research_cat(update, ctx, cat):
    uid = update.effective_user.id
    st = get_state(uid)
    tree = get_tree(st["country"], cat); researched = get_res(uid, cat)
    ctx.user_data["screen"] = f"research_{cat}"
    lines = [f"🔬 *{CAT_N[cat]}*","━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(tree):
        name, power, cost, build, steel, oil, desc = item
        if i == 0 or name in researched:
            lines.append(f"✅ *{name}* — قدرت {power}")
        else:
            # چک کن قبلی‌ها تحقیق شدن
            ok, need = research_chain_ok(uid, cat, i, tree, researched)
            if not ok:
                lines.append(f"🔒 *{name}* (ابتدا {need} را تحقیق کن)")
            else:
                lines.append(
                    f"🔓 *{name}*\n"
                    f"   📝 {desc}\n"
                    f"   💪 {power} | 🔬 {cost}💰+{build}نوبت | ⚙️{steel} 🛢️{oil}"
                )
    lines.append("\n👇 روی مدل بزن")
    await update.message.reply_text("\n".join(lines),
        reply_markup=kb_models(st["country"], cat, uid), parse_mode="Markdown")

# ─── ۴. امور کشور گسترده ───
def kb_internal_for(uid):
    st = get_state(uid)
    rows = []
    if st and st.get("protest"):
        rows.append([KeyboardButton("🚔 سرکوب اعتراض")])
    rows.append([KeyboardButton("👥 امور مردم")])
    rows.append([KeyboardButton("🏛️ امور حکومت")])
    rows.append([KeyboardButton("🏢 دولت")])
    rows.append([KeyboardButton("📊 مشکلات")])
    rows.append([KeyboardButton("📈 تورم")])
    rows.append([KeyboardButton("🕵️ نظارت بر مردم")])
    if st and st["country"] == "germany" and st.get("gov") == "nazism":
        rows.append([KeyboardButton("⚫ هولوکاست")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

async def on_internal(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    last = int(gget(f"last_int_{uid}", "0") or 0)
    turns_since = st["turn"] - last if last else 0
    t = (f"🏛️ *امور کشور*\n"
         f"😊 رضایت: {int(st['happiness'])}%\n"
         f"🕵️ نظارت: {st.get('surveillance',20)}%\n")
    if st.get("protest"):
        t += f"🔥 اعتراض فعال ({st.get('protest_t',0)} نوبت)"
    if turns_since >= 15:
        t += f"\n\n⚠️ *{turns_since} نوبت بی‌اقدام* — رضایت افتاده"
    t += "\n\n👇 بخش مورد نظر:"
    await update.message.reply_text(t,
        reply_markup=kb_internal_for(uid), parse_mode="Markdown")

async def on_int_action(update, ctx, cost, sat_gain, title, desc):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    if not pay(uid, money=cost):
        await update.message.reply_text(f"❌ نیاز: {cost}💰")
        return
    sset(uid, happiness=min(100, st["happiness"]+sat_gain))
    gset(f"last_int_{uid}", str(st["turn"]))
    await update.message.reply_text(
        f"{title}\n\n{desc}\n\n😊 رضایت: +{sat_gain}",
        reply_markup=kb_main())

async def on_people_affairs(update, ctx):
    uid = update.effective_user.id
    await update.message.reply_text(
        "👥 *امور مردم*\n\nچه خدمتی به مردم می‌دی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🏥 بیمارستان جدید"),KeyboardButton("📚 مدرسه جدید")],
            [KeyboardButton("💧 سیستم آب"),KeyboardButton("🏠 مسکن")],
            [KeyboardButton("🍞 سهمیه غذا")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_gov_affairs(update, ctx):
    await update.message.reply_text(
        "🏛️ *امور حکومت*\n\nچه اصلاحی انجام می‌دی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📜 اصلاحات مدنی"),KeyboardButton("⚖️ قضایی")],
            [KeyboardButton("💰 مبارزه با فساد"),KeyboardButton("📻 تبلیغات")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_state_affairs(update, ctx):
    await update.message.reply_text(
        "🏢 *دولت*\n\nچه کاری برای دستگاه دولتی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("💼 برنامه اشتغال"),KeyboardButton("🏗️ زیرساخت")],
            [KeyboardButton("📋 خدمت اجباری")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_problems(update, ctx):
    await update.message.reply_text(
        "📊 *مشکلات*\n\nکدوم مشکل رو حل کنی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🚨 مبارزه با جرم"),KeyboardButton("🏭 بیکاری")],
            [KeyboardButton("🚧 اعتراضات")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

async def on_inflation(update, ctx):
    await update.message.reply_text(
        "📈 *تورم*\n\nسیاست اقتصادی؟",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("💰 کاهش مالیات"),KeyboardButton("📉 کنترل قیمت‌ها")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True), parse_mode="Markdown")

# ─── ۵. بمب تزار = فتح کامل ───
async def apply_item_effect(ctx, uid, item_key, target_uid=None):
    st = get_state(uid)
    if not st: return "❌ خطا"
    c = COUNTRIES[st["country"]]
    result = "✅"
    # آیتم‌های بدون هدف
    if item_key in ("carpet_bomb", "war_speech", "war_storm", "revive",
                    "god_shield", "invisible", "double_attack", "lock_on",
                    "revenge", "seize_power"):
        if item_key == "carpet_bomb":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], happiness=max(0, ps["happiness"]-10))
            result = "🔥 بمباران قالی"
        elif item_key == "war_speech":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps: sset(p["uid"], money=max(0, ps["money"]*0.5))
            result = "📢 نطق جنگی"
        elif item_key == "war_storm":
            conn = db()
            conn.execute("DELETE FROM wars WHERE def_uid=?", (uid,))
            conn.commit(); conn.close()
            sset(uid, war=0)
            result = "🌪 طوفان جنگی"
        elif item_key == "revive":
            add_effect(uid, "revive", 999); result = "🔄 برگشت فوری"
        elif item_key == "god_shield":
            add_effect(uid, "shield", 60); result = "🛡 سپر جان"
        elif item_key == "invisible":
            add_effect(uid, "invisible", 30); result = "👻 نامرئی"
        elif item_key == "double_attack":
            add_effect(uid, "double_attack", 10); result = "⚡ دوبرابر حمله"
        elif item_key == "lock_on":
            add_effect(uid, "lock_on", 10); result = "🎯 قفل"
        elif item_key == "revenge":
            add_effect(uid, "revenge", 999); result = "💀 انتقام"
        elif item_key == "seize_power":
            add_effect(uid, "commander", 10); result = "👑 غصب قدرت"
        add_news(st["turn"], "item", result)
        return result
    # بمب تزار = فتح کامل
    if item_key == "tsar_bomb" and target_uid:
        ts = get_state(target_uid)
        if ts:
            # انتقال ۵۰٪ (چون بمب زدیم)
            sset(uid,
                 money=st["money"] + int(ts["money"]*0.5),
                 steel=st["steel"] + int(ts["steel"]*0.5),
                 oil=st["oil"] + int(ts["oil"]*0.5),
                 food=st["food"] + int(ts["food"]*0.5),
                 coal=st["coal"] + int(ts["coal"]*0.5),
                 water=st["water"] + int(ts["water"]*0.5),
                 manpower=st["manpower"] + int(ts["manpower"]*0.5),
                 soldiers=st["soldiers"] + int(ts["soldiers"]*0.5),
                 happiness=int((st["happiness"]+ts["happiness"])/2))
            # انتقال تحقیقات
            conn = db()
            rows = conn.execute("SELECT category,model FROM research WHERE user_id=?", (target_uid,)).fetchall()
            for r in rows:
                conn.execute("INSERT OR IGNORE INTO research(user_id,category,model) VALUES(?,?,?)",
                    (uid, r["category"], r["model"]))
            conn.commit(); conn.close()
            # کشتن
            sset(target_uid, dead=1)
            msg = (f"💣 *بمب تزار*\n\n"
                   f"بمب تزار توسط {c['n']} بر فراز پایتخت "
                   f"{COUNTRIES[ts['country']]['n']} منفجر شد. شهر کاملاً "
                   f"نابود شد و کشور فتح گردید.\n\n"
                   f"📊 {c['n']} ۵۰٪ دارایی‌ها + تحقیقات را به دست آورد.")
            add_news(st["turn"], "conquest", msg)
            try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
            except: pass
            result = f"💣 بمب تزار — {COUNTRIES[ts['country']]['n']} فتح شد."
    elif item_key == "force_exile" and target_uid:
        ts = get_state(target_uid)
        if ts: sset(target_uid, dead=1); result = "🗳 اخراج اجباری"
    elif item_key == "censor" and target_uid:
        add_effect(target_uid, "censored", 3); result = "🤐 سانسور"
    elif item_key == "expose" and target_uid:
        result = f"🕵️ افشاگری: {render_stats(target_uid)}"
    elif item_key == "force_ally" and target_uid:
        aid = get_user_alliance(uid)
        if not aid:
            conn = db()
            cur = conn.execute("INSERT INTO alliances(name,founder) VALUES(?,?)", (f"اتحاد {c['n']}", uid))
            aid = cur.lastrowid
            conn.execute("INSERT INTO allies(aid,user_id) VALUES(?,?)", (aid, uid))
            conn.commit(); conn.close()
        conn = db()
        conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)", (aid, target_uid))
        conn.commit(); conn.close()
        result = "🤝 اتحاد اجباری"
    elif item_key == "plunder" and target_uid:
        ts = get_state(target_uid)
        if ts:
            half = ts["money"]//2
            sset(target_uid, money=ts["money"]-half)
            sset(uid, money=st["money"]+half)
            result = f"💰 غارت {fmt(half)}"
    elif item_key == "nuke_item" and target_uid:
        result = use_atomic(uid, target_uid)
    elif item_key == "bio_weapon" and target_uid:
        add_effect(target_uid, "no_attack", 5)
        result = "☠️ بیولوژیک"
    elif item_key == "ballistic" and target_uid:
        ts = get_state(target_uid)
        if ts: sset(target_uid, dead=1); result = "🚀 بالستیک"
    add_news(st["turn"], "item", result)
    return result

# ─── ۶. فیلتر کانال: هیچ اطلاعات شخصی ───
async def post_to_channel(ctx, text):
    """فقط اخبار عمومی و بدون اطلاعات شخصی"""
    # لیست کلمات ممنوعه
    forbidden = ["پول تو", "سرباز تو", "ارتش تو", "منابعت", "جاسوس تو"]
    for w in forbidden:
        if w in text:
            return
    try:
        await ctx.bot.send_message(NEWS_CH, text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"news: {e}")

# ─── ۷. hook روتر ───
_old_on_text7 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text7(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    # کیبورد اصلی جدید
    if text == "💵 مالیات":
        await on_tax(update, ctx); return
    # اقتصاد حذف شد
    if text == "💰 اقتصاد":
        await update.message.reply_text("ℹ️ این بخش حذف شد. از 💵 مالیات استفاده کن.")
        return
    # امور کشور
    if text == "🏛️ امور کشور":
        await on_internal(update, ctx); return
    if text == "👥 امور مردم":
        await on_people_affairs(update, ctx); return
    if text == "🏛️ امور حکومت":
        await on_gov_affairs(update, ctx); return
    if text == "🏢 دولت":
        await on_state_affairs(update, ctx); return
    if text == "📊 مشکلات":
        await on_problems(update, ctx); return
    if text == "📈 تورم":
        await on_inflation(update, ctx); return
    # اقدامات
    acts = {
        "🏥 بیمارستان جدید": (500, 5, "🏥 بیمارستان جدید", "بیمارستان مدرن افتتاح شد."),
        "📚 مدرسه جدید": (400, 4, "📚 مدرسه جدید", "مدارس جدید ساخته شدند."),
        "💧 سیستم آب": (600, 6, "💧 سیستم آب", "آب سالم به همه رسید."),
        "🏠 مسکن": (700, 7, "🏠 مسکن", "پروژه مسکن عمومی آغاز شد."),
        "🍞 سهمیه غذا": (400, 5, "🍞 سهمیه غذا", "سهمیه غذایی توزیع شد."),
        "📜 اصلاحات مدنی": (600, 6, "📜 اصلاحات مدنی", "قوانین مدنی اصلاح شد."),
        "⚖️ قضایی": (500, 5, "⚖️ قضایی", "سیستم قضایی تقویت شد."),
        "💰 مبارزه با فساد": (800, 8, "💰 مبارزه با فساد", "فساد اداری سرکوب شد."),
        "📻 تبلیغات": (500, 5, "📻 تبلیغات", "رسانه‌ها در خدمت دولت."),
        "💼 برنامه اشتغال": (900, 9, "💼 برنامه اشتغال", "فرصت‌های شغلی جدید."),
        "🏗️ زیرساخت": (800, 7, "🏗️ زیرساخت", "پروژه‌های زیربنایی آغاز شد."),
        "🚨 مبارزه با جرم": (700, 6, "🚨 مبارزه با جرم", "نیروهای پلیس تقویت شدند."),
        "🏭 بیکاری": (900, 8, "🏭 بیکاری", "کارخانه‌های جدید افتتاح."),
        "🚧 اعتراضات": (500, 5, "🚧 اعتراضات", "کانال‌های گفتگو با معترضان."),
        "💰 کاهش مالیات": (0, 3, "💰 کاهش مالیات", "مالیات کمی کاهش یافت."),
        "📉 کنترل قیمت‌ها": (600, 6, "📉 کنترل قیمت‌ها", "قیمت‌ها کنترل شد."),
    }
    if text in acts:
        cost, sat, title, desc = acts[text]
        await on_int_action(update, ctx, cost, sat, title, desc)
        return
    return await _old_on_text7(update, ctx)

# ─── ۸. neglect در نوبت ───
_old_pt8 = process_turn

def process_turn(uid):
    res = _old_pt8(uid)
    if not res: return res
    st = get_state(uid)
    if not st: return res
    last = int(gget(f"last_int_{uid}", "0") or 0)
    if last == 0:
        gset(f"last_int_{uid}", str(st["turn"]))
    elif st["turn"] - last >= 15:
        sset(uid, happiness=max(0, st["happiness"]-3))
    return res

# ─── ۹. مقدار مالیات تو process_turn (۱-۱۰۰) ───
_old_calc_hap9 = calc_hap_delta

def calc_hap_delta(uid, st):
    d = 0
    tax = st.get("tax", 20)
    # مالیات ۱-۱۰۰
    if tax >= 80: d -= 15
    elif tax >= 60: d -= 10
    elif tax >= 40: d -= 5
    elif tax >= 25: d -= 2
    elif tax <= 10: d += 3
    f = st.get("food", 0)
    if f < 100: d -= 5
    elif f < 300: d -= 2
    elif f > 3000: d += 2
    w = st.get("water", 0)
    if w < 50: d -= 4
    if st.get("steel", 0) < 50: d -= 2
    if st.get("oil", 0) <= 0: d -= 3
    if st.get("coal", 0) < 50: d -= 2
    if st.get("war"): d -= 3
    if st.get("protest"): d -= 4
    if st.get("suppress_cd", 0) > 0: d -= 2
    d -= st.get("surveillance", 20) // 15
    d += GOVS.get(st.get("gov"), ("",0))[1]
    facs = len(get_fact(uid))
    if facs < 3: d -= 2
    elif facs > 6: d += 1
    for pk in get_done_proj(uid):
        p = PROJECTS.get(pk, {})
        if p.get("eff") == "happiness": d += p.get("v",0)//3
    if "conscription" in get_done_proj(uid): d -= 3
    if st.get("money", 0) <= 100: d -= 3
    if is_vip(uid) and d < 0: d = int(d/2)
    return d

# ─── ۱۰. چک زنجیره تحقیق ───
_old_on_text10 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text10(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    st = get_state(uid)
    if not st:
        return await _old_on_text10(update, ctx)
    screen = ctx.user_data.get("screen", "menu")
    # تحقیق زنجیره‌ای
    if screen.startswith("research_"):
        cat = screen.split("_", 1)[1]
        tree = get_tree(st["country"], cat)
        researched = get_res(uid, cat)
        for i, item in enumerate(tree):
            if len(item) < 7: continue
            name, power, cost, build, steel, oil, desc = item
            if name == text:
                if i == 0:
                    await update.message.reply_text("این مدل از اول باز است.")
                    return
                if name in researched:
                    await update.message.reply_text("قبلاً تحقیق شده.")
                    return
                # چک زنجیره
                ok, need = research_chain_ok(uid, cat, i, tree, researched)
                if not ok:
                    await update.message.reply_text(
                        f"🔒 ابتدا باید *{need}* را تحقیق کنی.",
                        parse_mode="Markdown")
                    return
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰")
                    return
                conn = db()
                conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
                    (uid, "research_pending", f"{cat}:{name}", 1, build))
                conn.commit(); conn.close()
                await update.message.reply_text(
                    f"🔬 *{name}* در صف تحقیق!\n⏱️ {build} نوبت\n💰 {cost}",
                    reply_markup=kb_main(), parse_mode="Markdown")
                return
    return await _old_on_text10(update, ctx)# ═══════════════════════════════════════════════════════════════
#  🩹 پچ ۴ — اتم تو ارتش، بدون منوی جدا
# ═══════════════════════════════════════════════════════════════

# ─── کیبورد اصلی بدون اتم ───
def kb_main():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 اقتصاد"),KeyboardButton("⚔️ ارتش")],
        [KeyboardButton("🔬 تحقیقات"),KeyboardButton("🏭 کارخونه‌ها")],
        [KeyboardButton("🤝 دیپلماسی"),KeyboardButton("📦 تجارت")],
        [KeyboardButton("🎯 حمله"),KeyboardButton("🕵️ جاسوسی")],
        [KeyboardButton("💵 مالیات"),KeyboardButton("🏛️ امور کشور")],
        [KeyboardButton("📊 آمار کامل")]],resize_keyboard=True)

# ─── کیبورد ارتش داینامیک ───
def kb_army_for(uid):
    st = get_state(uid)
    if not st:
        return kb_army()
    rows = [
        [KeyboardButton("🪖 سرباز"),KeyboardButton("🛡️ تانک")],
        [KeyboardButton("✈️ جنگنده"),KeyboardButton("🚀 جت")],
        [KeyboardButton("🚢 کشتی"),KeyboardButton("🎯 موشک")],
        [KeyboardButton("💣 بمب‌افکن"),KeyboardButton("🛡️ پدافند")],
        [KeyboardButton("✈️ بمباران"),KeyboardButton("📋 خدمت اجباری")],
    ]
    # دکمه اتم - شرط:
    # ۱. نوبت >= ATOMIC_UNLOCK
    # ۲. یا کشور آلمان/آمریکا، یا اتم قبلاً استفاده شده
    turn = st["turn"]
    can_show = False
    if turn >= ATOMIC_UNLOCK:
        if st["country"] in ("germany", "usa"):
            can_show = True
        elif gget("atomic_used") == "true":
            can_show = True
    if can_show:
        rows.append([KeyboardButton("☢️ پروژه اتمی")])
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

# ─── on_army با کیبورد داینامیک ───
async def on_army(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    await update.message.reply_text(
        f"⚔️ *ارتش {COUNTRIES[st['country']]['n']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚔️ قدرت حمله: {fmt(calc_power(uid,'attack'))}\n"
        f"🛡️ قدرت دفاع: {fmt(calc_power(uid,'defense'))}\n"
        f"🪖 سرباز: {fmt(st['soldiers'])}\n"
        f"🛡 پدافند: {fmt(get_aa_power(uid))}",
        reply_markup=kb_army_for(uid), parse_mode="Markdown")

# ─── on_atomic جدید — بدون شرط ادمین برای باز شدن ───
async def on_atomic(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    # شرط اصلی: نوبت >= ۱۰۷۷
    if st["turn"] < ATOMIC_UNLOCK:
        await update.message.reply_text(
            f"🔒 *پروژه اتمی*\n\nهنوز باز نشده.\n"
            f"باز شدن: نوبت {ATOMIC_UNLOCK}\n"
            f"الان: نوبت {st['turn']}\n"
            f"مانده: {ATOMIC_UNLOCK - st['turn']} نوبت",
            parse_mode="Markdown")
        return
    # شرط دوم: آلمان/آمریکا یا اولین استفاده شده
    if st["country"] not in ("germany", "usa") and gget("atomic_used") != "true":
        await update.message.reply_text(
            "🔒 این پروژه فقط برای آلمان و آمریکا در دسترس است.\n"
            "بعد از اولین استفاده در جهان، برای همه باز می‌شود.")
        return
    stage = st.get("atomic_stage", 0)
    if stage >= 3:
        await update.message.reply_text(
            f"☢️ *بمب اتمی آماده!*\n"
            f"تعداد بمب: {st.get('atomic_bombs',0)}\n\n"
            f"آماده استفاده از طریق منوی بمباران یا ادمین.",
            reply_markup=kb_army_for(uid), parse_mode="Markdown")
        return
    s = ATOMIC_STAGES[stage]
    await update.message.reply_text(
        f"☢️ *پروژه اتمی*\n"
        f"مرحله {stage+1}/3: {s['n']}\n\n"
        f"⏱️ {s['t']} نوبت\n"
        f"💰 {s['m']}\n⚙️ {s['s']}\n🛢️ {s['o']}\n\n"
        f"برای شروع، دکمه «☢️ شروع مرحله» را بزن.",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("☢️ شروع مرحله")],
            [KeyboardButton("🔙 منو")]],
            resize_keyboard=True), parse_mode="Markdown")

async def on_atomic_start(update, ctx):
    uid = update.effective_user.id
    st = get_state(uid)
    if not st: return
    if st["turn"] < ATOMIC_UNLOCK:
        await update.message.reply_text("🔒 هنوز باز نشده.")
        return
    if st["country"] not in ("germany", "usa") and gget("atomic_used") != "true":
        await update.message.reply_text("🔒 در دسترس نیست.")
        return
    stage = st.get("atomic_stage", 0)
    if stage >= 3: return
    s = ATOMIC_STAGES[stage]
    if not pay(uid, money=s["m"], steel=s["s"], oil=s["o"]):
        await update.message.reply_text("❌ منابع کافی نیست.")
        return
    sset(uid, atomic_t=s["t"])
    await update.message.reply_text(
        f"✅ {s['n']} شروع شد! ({s['t']} نوبت)",
        reply_markup=kb_army_for(uid))

# ─── hook روتر ───
_old_on_text4 = on_text

async def on_text(update, ctx):
    if not update.message or not update.message.text:
        return await _old_on_text4(update, ctx)
    text = update.message.text.strip()
    uid = update.effective_user.id
    # دکمه‌های اتم جدید
    if text == "☢️ پروژه اتمی":
        await on_atomic(update, ctx); return
    if text == "☢️ شروع مرحله":
        await on_atomic_start(update, ctx); return
    # منوی قدیمی حذف شده
    if text == "☢️ اتم":
        await update.message.reply_text(
            "ℹ️ این گزینه به بخش «⚔️ ارتش» منتقل شد.")
        return
    return await _old_on_text4(update, ctx)

# ─── وقتی اتم استفاده شد، پیام به همه + باز شدن برای همه ───
def use_atomic(uid, target_uid):
    st = get_state(uid); ts = get_state(target_uid)
    if not st or not ts: return "❌ خطا"
    if st.get("atomic_bombs", 0) <= 0:
        return "❌ بمب اتمی نداری."
    sset(uid, atomic_bombs=st["atomic_bombs"]-1)
    sset(target_uid, happiness=max(0, ts["happiness"]//2),
         soldiers=int(ts["soldiers"]*0.5))
    add_effect(target_uid, "no_attack", 3)
    first_time = (gget("atomic_used") != "true")
    gset("atomic_used", "true")
    add_news(st["turn"], "atomic",
        f"☢️ اولین بمب اتمی تاریخ توسط {COUNTRIES[st['country']]['n']} "
        f"بر فراز پایتخت {COUNTRIES[ts['country']]['n']} منفجر شد.")
    # اگه اولین بار بود، همه رو آگاه کن
    if first_time:
        for p in all_players():
            add_news(int(gget("turn","1")), f"atom_open_{p['uid']}",
                f"☢️ اولین بمب اتم جهان استفاده شد! "
                f"پروژه اتمی برای همه کشورها باز شد.")
    return f"☢️ بمب اتمی {COUNTRIES[ts['country']]['n']} را هدف گرفت."

# ─── تحویل پیام باز شدن اتم ───
_old_deliver = deliver_pending

async def deliver_pending(ctx):
    for p in all_players():
        uid = p["uid"]
        key = f"msg_read_{uid}"
        last_read = int(gget(key, "0") or 0)
        conn = db()
        rows = conn.execute(
            "SELECT * FROM news WHERE id>? AND "
            "(cat=? OR cat=? OR cat=? OR cat=? OR cat=? OR cat=?) ORDER BY id",
            (last_read, f"spy_ok_{uid}", f"spy_fail_{uid}",
             f"spy_caught_{uid}", f"ally_war_{uid}",
             f"conquest_{uid}", f"atom_open_{uid}")).fetchall()
        conn.close()
        for r in rows:
            try:
                if r["cat"].startswith("spy_ok_"):
                    await ctx.bot.send_message(uid,
                        f"✅ *جاسوسی موفق!*\n━━━━━━━━━━━━━━━━\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_fail_"):
                    await ctx.bot.send_message(uid,
                        f"❌ *جاسوس لو رفت!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("spy_caught_"):
                    await ctx.bot.send_message(uid,
                        f"🚨 *هشدار امنیتی!*\n{r['text']}",
                        parse_mode="Markdown")
                elif r["cat"].startswith("ally_war_"):
                    await ctx.bot.send_message(uid,
                        f"⚠️ *هشدار اتحاد!*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                elif r["cat"].startswith("conquest_"):
                    await ctx.bot.send_message(uid,
                        f"💀 *اطلاعیه*\n\n{r['text']}",
                        parse_mode="Markdown", reply_markup=kb_main())
                elif r["cat"].startswith("atom_open_"):
                    await ctx.bot.send_message(uid,
                        f"☢️ *اطلاعیه مهم*\n\n{r['text']}\n\n"
                        f"از این پس، پروژه اتمی در بخش «⚔️ ارتش» برای تو هم باز است.",
                        parse_mode="Markdown")
                last_read = r["id"]
            except: pass
        gset(key, str(last_read))
