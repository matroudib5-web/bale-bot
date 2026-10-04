#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3, random, logging, asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus
try:
    from keep_alive import keep_alive
except ImportError:
    def keep_alive(): pass

BOT_TOKEN = "152004939:-yVJrAHZWHVeopSTZUUltAAIkdjE3f7qNm8"
BALE_API = "https://tapi.bale.ai/bot"
DB_FILE = "ww2.db"
TURN_MINUTES = 30
TOTAL_TURNS = 2193
ATTACK_UNLOCK = 10
ATOMIC_UNLOCK = 1077
UN_INTERVAL = 10
NEWS_CH = "@WORLDWAR21250"
ADMIN_IDS = [1429506412, 1618371215]
CHANNELS = [{"u":"@Hitlerss1","l":"📢 کانال اول"},{"u":"@WORLDWAR21250","l":"📢 کانال دوم"}]
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

COUNTRIES = {
"germany":{"f":"🇩🇪","n":"آلمان","gov":"fascist","m":10000,"fo":5000,"s":500,"o":100,"c":500,"mp":5000,"bm":150,"bf":100,"bs":30,"bo":8,"bc":25},
"uk":{"f":"🇬🇧","n":"انگلیس","gov":"constitutional_monarchy","m":10000,"fo":5000,"s":400,"o":150,"c":400,"mp":4000,"bm":120,"bf":90,"bs":22,"bo":12,"bc":20},
"usa":{"f":"🇺🇸","n":"آمریکا","gov":"liberal_democracy","m":15000,"fo":8000,"s":800,"o":500,"c":800,"mp":8000,"bm":200,"bf":150,"bs":40,"bo":30,"bc":35},
"ussr":{"f":"🇷🇺","n":"شوروی","gov":"communism","m":10000,"fo":6000,"s":600,"o":300,"c":700,"mp":10000,"bm":130,"bf":110,"bs":32,"bo":18,"bc":30},
"france":{"f":"🇫🇷","n":"فرانسه","gov":"parliamentary_republic","m":8000,"fo":4000,"s":350,"o":80,"c":300,"mp":3500,"bm":110,"bf":85,"bs":20,"bo":6,"bc":18},
"japan":{"f":"🇯🇵","n":"ژاپن","gov":"military_dictatorship","m":8000,"fo":4000,"s":350,"o":80,"c":300,"mp":5000,"bm":115,"bf":80,"bs":21,"bo":5,"bc":15},
"italy":{"f":"🇮🇹","n":"ایتالیا","gov":"fascist","m":7000,"fo":3500,"s":250,"o":50,"c":200,"mp":3000,"bm":100,"bf":75,"bs":16,"bo":4,"bc":12},
"china":{"f":"🇨🇳","n":"چین","gov":"single_party","m":5000,"fo":5000,"s":150,"o":30,"c":150,"mp":12000,"bm":70,"bf":120,"bs":8,"bo":2,"bc":8},
"poland":{"f":"🇵🇱","n":"لهستان","gov":"parliamentary_republic","m":5000,"fo":3000,"s":200,"o":40,"c":250,"mp":2500,"bm":80,"bf":70,"bs":14,"bo":3,"bc":14},
"canada":{"f":"🇨🇦","n":"کانادا","gov":"constitutional_monarchy","m":6000,"fo":4000,"s":300,"o":120,"c":400,"mp":2000,"bm":95,"bf":85,"bs":18,"bo":10,"bc":20},
"australia":{"f":"🇦🇺","n":"استرالیا","gov":"constitutional_monarchy","m":5000,"fo":3500,"s":250,"o":80,"c":300,"mp":1500,"bm":85,"bf":80,"bs":16,"bo":6,"bc":15},
"brazil":{"f":"🇧🇷","n":"برزیل","gov":"presidential_republic","m":5000,"fo":4500,"s":200,"o":60,"c":150,"mp":4000,"bm":75,"bf":95,"bs":12,"bo":5,"bc":9},
}
CMAP = {f"{c['f']} {c['n']}":k for k,c in COUNTRIES.items()}
CFA = {c['n']:k for k,c in COUNTRIES.items()}
GOVS = {
"absolute_monarchy":("👑 پادشاهی مطلقه",-2),"constitutional_monarchy":("👑 پادشاهی مشروطه",1),
"presidential_republic":("🗳️ جمهوری ریاستی",1),"parliamentary_republic":("🗳️ جمهوری پارلمانی",2),
"fascist":("🚩 فاشیسم",-3),"communism":("🚩 کمونیسم",-1),
"military_dictatorship":("⚙️ دیکتاتوری نظامی",-2),"personal_dictatorship":("⚙️ دیکتاتوری شخصی",-3),
"liberal_democracy":("🕊️ دموکراسی لیبرال",2),"social_democracy":("🕊️ دموکراسی اجتماعی",3),
"theocracy":("⚖️ تئوکراسی",-1),"single_party":("🚩 تک‌حزبی",-2),
}
def M(n,p,c,b,s,o,d): return (n,p,c,b,s,o,d)
R = {}
R["germany"]={
"tanks":[M("Panzer I",5,50,1,20,0,"سبک"),M("Panzer II",8,100,1,40,0,"شناسایی"),M("Panzer III",12,200,2,80,5,"متوسط"),M("Panzer IV",18,350,2,140,10,"اصلی"),M("Tiger I",28,700,3,250,20,"سنگین")],
"fighters":[M("Ar 68",6,50,1,15,5,"آموزشی"),M("Bf 109E",10,100,1,30,10,"اصلی"),M("Bf 109G",15,200,2,60,20,"برتر"),M("Fw 190",20,350,2,100,30,"سنگین"),M("Ta 152",26,600,3,180,45,"پیشرفته")],
"jets":[M("He 178",15,200,2,50,30,"اولین"),M("Me 262",30,500,3,150,60,"افسانه‌ای"),M("He 162",24,400,3,100,45,"Volks"),M("Ho 229",34,700,4,200,70,"بال‌پرنده"),M("Arado 234",32,650,4,180,65,"جت‌بمب")],
"ships":[M("U-Boat VII",14,100,3,40,10,"زیردریایی"),M("Scharnhorst",20,250,4,100,20,"رزمناو"),M("Bismarck",28,450,5,180,30,"ناو"),M("Tirpitz",32,600,6,220,40,"ناو"),M("Graf Zeppelin",36,750,7,280,50,"ناو‌هواپیمابر")],
"missiles":[M("V-1",12,150,2,30,20,"کروز"),M("V-2",24,400,3,80,40,"بالستیک"),M("V-3",30,600,4,120,55,"چندمرحله"),M("A9",38,900,5,200,80,"قاره‌پیما"),M("Silbervogel",42,1200,6,300,100,"فضایی")],
"bombers":[M("Do 17",8,80,2,25,15,"سبک"),M("He 111",12,150,2,50,25,"متوسط"),M("Ju 88",16,250,3,80,35,"چندنقش"),M("He 177",22,400,4,130,50,"سنگین"),M("Ju 390",28,700,5,200,70,"قاره‌پیما")],
"aa":[M("Flak 30",10,500,2,50,0,"۲۰mm"),M("Flakvierling",18,1000,3,100,0,"چهارلول"),M("Flak 43",25,2000,4,200,0,"۳۷mm"),M("Flak 36/37",45,5000,6,500,0,"۸۸mm"),M("Flak 40",80,25000,15,2500,0,"۱۲۸mm")]}
R["uk"]={
"tanks":[M("Vickers VI",5,50,1,20,0,"سبک"),M("Matilda II",12,200,2,80,5,"پیاده"),M("Churchill",20,400,3,150,15,"سنگین"),M("Cromwell",24,550,3,180,25,"سریع"),M("Comet",28,750,4,220,35,"برتر")],
"fighters":[M("Gladiator",6,50,1,15,5,"دوباله"),M("Hurricane",10,100,1,30,10,"اصلی"),M("Spitfire",16,250,2,70,20,"افسانه‌ای"),M("Typhoon",22,400,3,110,30,"سنگین"),M("Tempest",26,600,3,150,40,"برتر")],
"jets":[M("Gloster E.28",12,200,2,50,30,"اولین"),M("Meteor",26,500,3,140,55,"اصلی"),M("Vampire",24,480,3,130,50,"دوم"),M("Sea Vampire",28,600,4,160,60,"ناوبر"),M("Swift",32,800,4,200,75,"پیشرفته")],
"ships":[M("Tribal",10,100,3,30,10,"ناوشکن"),M("Nelson",22,300,4,120,25,"ناو"),M("King George V",28,450,5,180,35,"ناو"),M("Illustrious",30,600,6,220,45,"ناو‌هواپیمابر"),M("Vanguard",34,800,7,280,55,"برتر")],
"missiles":[M("UP-1",8,100,2,20,15,"ضدهوایی"),M("Stooge",12,200,2,40,25,"ضدکشتی"),M("Brakemine",18,350,3,70,35,"هدایت"),M("Green Cheese",24,500,4,100,50,"ضدکشتی"),M("Blue Steel",30,700,5,150,65,"بالستیک")],
"bombers":[M("Blenheim",8,80,2,25,15,"سبک"),M("Wellington",12,150,2,50,25,"متوسط"),M("Halifax",18,300,3,90,40,"سنگین"),M("Lancaster",24,450,4,130,50,"شبانه"),M("Lincoln",28,650,5,170,65,"قاره‌پیما")],
"aa":[M("Polsten",12,600,2,60,0,"۲۰mm"),M("Bofors",22,1200,3,120,0,"۴۰mm"),M("QF 3.7",55,7000,8,700,0,"۹۴mm"),M("QF 4.5",75,15000,12,1500,0,"۱۱۴mm")]}
R["usa"]={
"tanks":[M("M2 Light",6,50,1,20,0,"سبک"),M("M3 Stuart",10,150,1,60,5,"سبک"),M("M4 Sherman",18,350,2,130,20,"اصلی"),M("M26 Pershing",26,600,3,200,35,"سنگین"),M("M46 Patton",32,800,4,250,45,"برتر")],
"fighters":[M("P-36",6,50,1,15,5,"آموزشی"),M("P-40",10,120,1,35,10,"اصلی"),M("P-51",18,350,2,100,25,"برتر"),M("P-47",22,450,3,130,35,"سنگین"),M("P-80",30,750,4,200,55,"جت")],
"jets":[M("P-59",14,250,2,60,35,"اولیه"),M("P-80",28,550,3,160,60,"اصلی"),M("F-84",32,700,4,200,70,"جنگنده‌بمب"),M("F-86",38,900,5,260,85,"برتر"),M("F-89",36,850,5,240,80,"رهگیر")],
"ships":[M("Clemson",10,100,3,30,10,"ناوشکن"),M("Brooklyn",16,250,4,90,20,"رزمناو"),M("Essex",28,500,6,180,40,"ناو‌هواپیمابر"),M("Iowa",34,700,7,250,55,"ناو"),M("Midway",38,900,8,300,70,"ناو‌بزرگ")],
"missiles":[M("M8",8,80,2,15,10,"راکت"),M("Tiny Tim",14,200,2,40,25,"ضدکشتی"),M("Bat",20,400,3,70,40,"هدایت"),M("Loon",24,550,4,100,50,"کپیV-1"),M("Corporal",30,750,5,150,70,"بالستیک")],
"bombers":[M("B-10",8,80,2,25,15,"اولیه"),M("B-17",16,250,3,80,30,"قلعه"),M("B-24",20,350,3,100,40,"سنگین"),M("B-29",28,600,4,180,60,"ابرقدرت"),M("B-36",38,1000,6,300,100,"قاره‌پیما")],
"aa":[M("M2HB",10,500,2,50,0,"سبک"),M("Bofors M1",20,1200,3,120,0,"۴۰mm"),M("M3",30,2500,5,250,0,"۷۶mm"),M("M1",55,6000,7,600,0,"۹۰mm"),M("M45",80,15000,12,1500,0,"۱۲۰mm")]}
R["ussr"]={
"tanks":[M("T-26",5,50,1,20,0,"سبک"),M("BT-7",9,120,1,45,5,"سریع"),M("T-34",20,350,2,130,20,"افسانه‌ای"),M("KV-1",26,500,3,180,25,"سنگین"),M("IS-2",32,750,4,250,40,"برتر")],
"fighters":[M("I-15",6,50,1,15,5,"دوباله"),M("Yak-1",10,100,1,30,10,"اصلی"),M("La-5",16,250,2,70,20,"برتر"),M("Yak-9",20,400,2,100,30,"چندکاره"),M("La-9",26,600,3,150,45,"نهایی")],
"jets":[M("MiG-9",22,400,3,100,45,"اولیه"),M("Yak-15",20,380,3,90,40,"سبک"),M("La-15",26,500,4,130,55,"برتر"),M("MiG-15",36,800,5,200,80,"افسانه‌ای"),M("Il-28",32,700,4,180,70,"جت‌بمب")],
"ships":[M("Gnevny",10,100,3,30,10,"ناوشکن"),M("Kirov",18,300,4,110,25,"رزمناو"),M("Chapayev",24,450,5,160,35,"رزمناو"),M("Sovetsky",34,800,7,280,60,"ناو"),M("Kronshtadt",32,700,7,240,55,"سنگین")],
"missiles":[M("Katyusha",10,100,2,20,10,"توپخانه"),M("RS-82",14,200,2,40,20,"هواپایه"),M("10Kh",20,400,3,80,35,"کروز"),M("R-1",26,550,4,120,50,"کپیV-2"),M("R-5",32,800,5,180,70,"بالستیک")],
"bombers":[M("SB",8,80,2,25,15,"سریع"),M("DB-3",12,150,2,50,25,"دوربرد"),M("Pe-2",16,250,3,80,30,"شیرجه"),M("Tu-2",20,400,3,100,40,"متوسط"),M("Pe-8",26,600,5,150,55,"دوربرد")],
"aa":[M("72-K",8,400,2,40,0,"۲۵mm"),M("61-K",15,1000,3,100,0,"۳۷mm"),M("3-K",30,2500,5,250,0,"۷۶mm"),M("52-K",55,6000,7,600,0,"۸۵mm")]}
R["france"]={
"tanks":[M("FT-17",4,40,1,15,0,"قدیمی"),M("R-35",8,100,1,40,0,"پیاده"),M("H-39",10,150,2,55,5,"سواره"),M("Char B1",18,350,2,130,15,"سنگین"),M("ARL 44",24,550,3,180,30,"مدرن")],
"fighters":[M("MS.406",8,80,1,25,8,"اصلی"),M("MB.152",10,120,1,35,10,"سنگین"),M("D.520",14,200,2,55,15,"برتر"),M("VG.33",16,280,2,70,20,"پیشرفته"),M("NC.900",20,400,3,100,30,"مدرن")],
"jets":[M("SO.6000",12,250,3,60,35,"آزمایشی"),M("MD.450",22,500,4,130,55,"اولیه"),M("Mystere II",26,650,4,160,65,"برتر"),M("Mystere IV",30,800,5,200,80,"پیشرفته"),M("Vautour",32,900,5,240,90,"چندکاره")],
"ships":[M("Bourrasque",10,100,3,30,10,"ناوشکن"),M("La Galissonniere",16,250,4,90,20,"رزمناو"),M("Dunkerque",22,400,5,150,30,"ناو"),M("Richelieu",30,600,6,220,45,"برتر"),M("Jean Bart",32,750,7,260,55,"ناو")],
"missiles":[M("SE.4300",10,120,2,25,15,"آزمایشی"),M("SS.10",16,250,3,50,25,"ضدتانک"),M("SS.11",22,400,3,80,40,"ضدتانک"),M("MASURCA",28,600,4,130,55,"ضدهوایی"),M("Pluton",32,800,5,180,70,"بالستیک")],
"bombers":[M("MB.200",8,80,2,25,15,"بمب"),M("LeO 451",12,150,2,50,25,"متوسط"),M("Amiot 354",16,250,3,80,35,"سنگین"),M("NC.150",20,400,4,100,45,"دوربرد"),M("SO.4000",24,550,4,130,55,"جت")],
"aa":[M("Hotchkiss",12,600,2,60,0,"۲۵mm"),M("Schneider 75",35,3000,6,300,0,"۷۵mm"),M("Schneider 90",55,7000,8,700,0,"۹۰mm")]}
R["japan"]={
"tanks":[M("Type 89",5,50,1,20,0,"سبک"),M("Type 97",9,120,1,45,5,"متوسط"),M("Chi-He",14,250,2,80,10,"متوسط"),M("Chi-Nu",18,400,3,120,20,"برتر"),M("Chi-Ri",24,600,4,170,30,"سنگین")],
"fighters":[M("Ki-27",8,80,1,25,8,"سبک"),M("A6M Zero",14,200,2,55,15,"افسانه"),M("Ki-61",16,280,2,70,20,"Tony"),M("Ki-84",20,400,3,100,30,"Frank"),M("N1K",24,550,3,130,40,"Shiden")],
"jets":[M("Kikka",20,400,3,100,45,"اولیه"),M("Ki-201",24,550,4,130,55,"برتر"),M("J8M",18,380,3,80,40,"رهگیر"),M("J7W",28,700,5,180,70,"کانارد"),M("F-86 pl",32,900,5,240,85,"مدرن")],
"ships":[M("Fubuki",10,100,3,30,10,"ناوشکن"),M("Mogami",16,250,4,90,20,"رزمناو"),M("Shokaku",22,400,5,150,35,"ناو‌هواپیمابر"),M("Yamato",38,900,8,300,60,"ابرناو"),M("Shinano",36,800,7,280,55,"ناو‌بزرگ")],
"missiles":[M("Type 3",10,100,2,25,15,"راکت"),M("MXY7",14,200,2,40,20,"انسان"),M("Funryu",20,400,3,80,35,"ضدهوایی"),M("Ki-148",24,550,4,120,50,"هواپایه"),M("I-Go",28,700,5,150,65,"هدایت")],
"bombers":[M("Ki-21",8,80,2,25,15,"متوسط"),M("G3M",12,150,2,50,25,"دوربرد"),M("G4M",16,250,3,80,35,"معروف"),M("P1Y",20,400,4,100,45,"سریع"),M("G8N",26,600,5,150,55,"سنگین")],
"aa":[M("Type 98",10,500,2,50,0,"۲۰mm"),M("Type 96",18,1000,3,100,0,"۲۵mm"),M("Type 88",35,3000,6,300,0,"۷۵mm"),M("Type 14",55,7000,8,700,0,"۱۰۵mm"),M("Type 89",75,15000,12,1500,0,"۱۲۷mm")]}
R["italy"]={
"tanks":[M("L3",4,40,1,15,0,"سبک"),M("M13/40",10,150,2,55,5,"متوسط"),M("M14/41",12,200,2,65,8,"متوسط"),M("P26/40",18,350,3,120,15,"سنگین"),M("P43",22,500,4,150,25,"برتر")],
"fighters":[M("CR.42",6,50,1,15,5,"دوباله"),M("MC.200",10,120,1,35,10,"اصلی"),M("MC.202",14,250,2,55,18,"برتر"),M("MC.205",18,400,2,90,28,"نهایی"),M("Re.2005",22,550,3,130,40,"پیشرفته")],
"jets":[M("Campini",12,250,3,60,35,"آزمایشی"),M("G.80",20,450,4,110,50,"اولیه"),M("Sagittario",24,600,4,140,60,"برتر"),M("G.91",30,800,5,190,75,"تاکتیکی"),M("G.222",32,900,5,220,85,"ترابری")],
"ships":[M("Soldati",10,100,3,30,10,"ناوشکن"),M("Zara",18,300,4,110,25,"رزمناو"),M("Littorio",28,600,6,220,45,"ناو"),M("Aquila",26,500,6,180,40,"ناو‌هواپیمابر"),M("Impero",30,750,7,260,55,"ناو")],
"missiles":[M("Tipo A",8,100,2,20,12,"راکت"),M("Tipo B",14,220,3,45,22,"ضدتانک"),M("Tipo C",18,350,3,70,35,"هدایت"),M("Aria",24,500,4,110,50,"ضدهوایی"),M("Vega",28,700,5,150,65,"بالستیک")],
"bombers":[M("SM.79",8,80,2,25,15,"معروف"),M("Z.1007",12,150,2,50,25,"متوسط"),M("P.108",18,300,3,90,40,"سنگین"),M("SM.82",20,400,4,110,45,"ترابری"),M("BZ.308",24,550,4,130,55,"دوربرد")],
"aa":[M("Breda 35",10,500,2,50,0,"۲۰mm"),M("Scotti 39",16,900,3,90,0,"۲۰mm"),M("Cannone 37",25,2000,4,200,0,"۳۷mm"),M("Cannone 90",55,7000,8,700,0,"۹۰mm"),M("Cannone 102",70,13000,11,1300,0,"۱۰۲mm")]}
R["china"]={
"tanks":[M("Type 88",4,40,1,15,0,"قدیمی"),M("Type 24",8,100,1,40,0,"سبک"),M("Type 58",14,250,2,80,10,"متوسط"),M("Type 59",20,400,3,130,20,"متوسط"),M("Type 62",24,550,4,170,30,"سبک")],
"fighters":[M("Hawk III",8,80,1,25,8,"آمریکایی"),M("I-16",10,120,1,35,10,"شوروی"),M("P-40",14,220,2,55,15,"آمریکایی"),M("P-51",18,400,2,90,30,"برتر"),M("J-2",22,550,3,130,40,"جت")],
"jets":[M("J-2",18,400,3,90,40,"اولیه"),M("J-4",22,500,4,110,50,"میگ"),M("J-5",26,600,4,140,60,"برتر"),M("J-6",30,750,5,180,70,"میگ۱۹"),M("J-7",34,900,5,220,80,"پیشرفته")],
"ships":[M("Ning Hai",10,100,3,30,10,"سبک"),M("Ping Hai",10,100,3,30,10,"سبک"),M("Chao Ho",14,200,4,70,15,"رزمناو"),M("Hai Chi",18,300,5,110,25,"رزمناو"),M("Yat Sen",20,350,5,120,30,"رزمناو")],
"missiles":[M("Type 63",10,120,2,25,15,"راکت"),M("Type 70",14,220,3,45,22,"ضدتانک"),M("SY-1",20,400,3,80,35,"ضدکشتی"),M("HQ-1",24,550,4,120,50,"ضدهوایی"),M("DF-1",28,700,5,150,65,"بالستیک")],
"bombers":[M("Hawk b",6,80,2,20,12,"سبک"),M("B-10",12,180,2,50,25,"آمریکایی"),M("Tu-2",16,280,3,80,35,"شوروی"),M("Il-28",22,450,4,110,45,"جت"),M("H-6",28,700,5,180,60,"استراتژیک")],
"aa":[M("Type 88",35,3000,6,300,0,"۷۵mm")]}
R["poland"]={
"tanks":[M("TK-3",4,40,1,15,0,"سبک"),M("7TP",10,150,2,55,5,"متوسط"),M("10TP",12,200,2,65,8,"کریستی"),M("14TP",16,300,3,100,15,"متوسط"),M("PZInz 130",20,400,3,130,25,"آبی‌خاکی")],
"fighters":[M("PZL P.11",6,50,1,15,5,"دوباله"),M("PZL P.24",10,120,1,35,10,"صادراتی"),M("PZL.50",14,250,2,55,18,"جدید"),M("PZL.62",18,350,3,80,25,"پیشرفته"),M("PZL.55",22,500,3,110,35,"برتر")],
"jets":[M("TS-11",16,300,3,70,35,"آموزشی"),M("Lim-1",20,400,4,100,45,"میگ"),M("Lim-2",24,500,4,120,55,"میگ"),M("Lim-5",28,650,5,160,65,"میگ۱۷"),M("I-22",30,750,5,180,75,"پیشرفته")],
"ships":[M("Grom",10,100,3,30,10,"ناوشکن"),M("Blyskawica",12,150,3,45,12,"ناوشکن"),M("Orzel",14,220,4,60,15,"زیردریایی"),M("Wilk",14,200,4,55,15,"زیردریایی"),M("Conrad",18,300,5,100,25,"رزمناو")],
"missiles":[M("R-1",8,100,2,20,12,"راکت"),M("R-2",12,200,3,40,22,"موشک"),M("R-3",18,350,3,70,35,"ضدتانک"),M("R-4",22,500,4,100,45,"ضدهوایی"),M("R-5",26,650,5,130,60,"بالستیک")],
"bombers":[M("PZL.37",8,80,2,25,15,"متوسط"),M("PZL.49",14,220,3,55,25,"دوربرد"),M("LWS-6",12,180,2,50,22,"بمب"),M("PZL.30",16,280,3,70,32,"بمب"),M("PZL.42",20,400,4,100,40,"پیشرفته")],
"aa":[M("wz. 36",20,1200,3,120,0,"۴۰mm"),M("wz. 37",35,3000,6,300,0,"۷۵mm")]}
R["canada"]={
"tanks":[M("Ram I",14,250,2,80,10,"کانادایی"),M("Ram II",18,350,3,110,15,"پیشرفته"),M("Grizzly",20,400,3,130,20,"کانادایی"),M("Skink",22,450,4,140,22,"ضدهوایی"),M("Cougar",26,600,4,170,30,"برتر")],
"fighters":[M("Hurricane",10,100,1,30,10,"جنگنده"),M("Spitfire",14,220,2,55,18,"جنگنده"),M("Mustang",18,380,2,90,28,"جنگنده"),M("Sabre",26,650,4,150,55,"جت"),M("CF-100",30,800,5,190,70,"رهگیر")],
"jets":[M("CF-100",24,550,4,130,55,"رهگیر"),M("CF-101",28,700,5,170,65,"رهگیر"),M("CF-104",32,850,5,210,80,"مافوق"),M("CF-105",38,1000,6,260,90,"پیشرفته"),M("CF-116",30,800,5,190,75,"تاکتیکی")],
"ships":[M("Tribal",10,100,3,30,10,"ناوشکن"),M("River",12,150,3,45,12,"اسکورت"),M("Uganda",18,300,4,110,25,"رزمناو"),M("Bonaventure",26,500,6,180,40,"ناو‌هواپیمابر"),M("Magnificent",24,450,6,160,35,"ناو‌هواپیمابر")],
"missiles":[M("Velvet Glove",14,220,3,45,22,"هواپایه"),M("Sparrow",20,400,3,80,35,"ضدهوایی"),M("Sidewinder",24,500,4,100,45,"هواپایه"),M("Genie",26,600,4,120,55,"هواپایه"),M("Bomarc",30,750,5,150,65,"ضدهوایی")],
"bombers":[M("Bolingbroke",8,80,2,25,15,"بمب"),M("Hampden",12,150,2,50,25,"بمب"),M("Halifax",18,300,3,90,40,"بمب"),M("Lancaster",24,450,4,130,50,"بمب"),M("Canuck",28,650,5,170,60,"جت")],
"aa":[M("QF 3.7",55,7000,8,700,0,"۹۴mm")]}
R["australia"]={
"tanks":[M("Sentinel AC1",12,200,2,70,8,"استرالیایی"),M("Sentinel AC3",16,300,3,100,15,"پیشرفته"),M("Sentinel AC4",18,350,3,110,18,"برتر"),M("Matilda",20,400,3,130,22,"پیاده"),M("Centurion",26,600,4,170,30,"برتر")],
"fighters":[M("Wirraway",8,80,1,25,8,"آموزشی"),M("Boomerang",12,180,2,45,15,"استرالیایی"),M("Spitfire",16,250,2,65,20,"جنگنده"),M("Mustang",20,400,2,100,30,"جنگنده"),M("Sabre",28,700,4,160,60,"جت")],
"jets":[M("CAC Sabre",26,600,4,140,55,"جت"),M("Mirage III",30,750,5,180,70,"برتر"),M("F-111",34,900,5,230,85,"بمب"),M("F/A-18",38,1000,6,260,90,"چندکاره"),M("F-35",42,1200,6,300,100,"نسل۵")],
"ships":[M("Perth",10,100,3,30,10,"رزمناو"),M("Shropshire",14,220,4,70,18,"رزمناو"),M("Sydney",16,280,4,85,22,"رزمناو"),M("Melbourne",24,450,6,160,35,"ناو‌هواپیمابر"),M("Vengeance",22,400,6,140,30,"ناو‌هواپیمابر")],
"missiles":[M("Ikara",16,250,3,50,25,"ضدزیردریایی"),M("Sea Cat",20,400,3,80,35,"ضدهوایی"),M("Rapier",24,500,4,100,45,"ضدهوایی"),M("Harpoon",28,650,4,140,55,"ضدکشتی"),M("Sidewinder",26,600,4,120,50,"هواپایه")],
"bombers":[M("Beaufort",8,80,2,25,15,"بمب"),M("Beaufighter",12,150,2,50,25,"سنگین"),M("Lincoln",20,400,4,100,45,"بمب"),M("Canberra",26,600,4,150,55,"جت"),M("F-111",32,850,5,200,80,"جت")],
"aa":[M("QF 3.7",55,7000,8,700,0,"۹۴mm")]}
R["brazil"]={
"tanks":[M("M3 Stuart",10,150,1,55,5,"سبک"),M("M4 Sherman",18,350,2,120,18,"متوسط"),M("M41 Walker",22,450,3,140,25,"سبک"),M("EE-9",20,400,3,130,22,"زرهی"),M("EE-T1",28,650,4,180,35,"برتر")],
"fighters":[M("P-36",8,80,1,25,8,"جنگنده"),M("P-40",12,180,2,45,15,"جنگنده"),M("P-47",16,280,2,70,22,"سنگین"),M("F-80",24,500,4,120,45,"جت"),M("Mirage III",30,750,5,180,70,"برتر")],
"jets":[M("F-80",22,450,4,110,45,"اولیه"),M("F-86",28,650,5,150,60,"برتر"),M("Mirage III",32,800,5,190,75,"مافوق"),M("F-5",30,750,5,180,70,"سبک"),M("AMX",34,900,6,220,85,"تهاجمی")],
"ships":[M("Bahia",10,100,3,30,10,"رزمناو"),M("Minas Geraes",16,250,4,90,20,"ناو"),M("Sao Paulo",18,300,5,110,25,"ناو"),M("Riachuelo",14,220,4,70,18,"رزمناو"),M("Rio",16,280,4,85,22,"رزمناو")],
"missiles":[M("SS.10",12,200,3,40,22,"ضدتانک"),M("SS.11",16,280,3,55,30,"ضدتانک"),M("MAA-1",22,450,4,90,40,"هواپایه"),M("AVibras",26,600,4,120,50,"تاکتیکی"),M("Mectron",30,750,5,150,65,"ضدکشتی")],
"bombers":[M("B-25",10,120,2,35,18,"متوسط"),M("B-17",16,280,3,70,30,"سنگین"),M("B-24",18,320,3,85,35,"دوربرد"),M("B-26",14,220,3,55,22,"بمب"),M("AMX",24,500,4,110,45,"جت")],
"aa":[M("3.7 inch",55,7000,8,700,0,"۹۴mm")]}

CAT_N = {"tanks":"🛡️ تانک","fighters":"✈️ جنگنده","jets":"🚀 جت","ships":"🚢 کشتی/ناو","missiles":"🎯 موشک","bombers":"💣 بمب‌افکن","aa":"🛡️ پدافند"}
PROJECTS = {
"steel_mill":{"n":"⚙️ کارخانه فولاد","cat":"industry","m":400,"s":80,"d":4,"eff":"steel","v":30},
"ammo_factory":{"n":"🔫 کارخانه مهمات","cat":"industry","m":300,"s":60,"d":3,"eff":"equip","v":20},
"coal_mine":{"n":"⛏️ معدن زغال","cat":"energy","m":350,"s":50,"d":3,"eff":"coal","v":25},
"refinery":{"n":"🛢️ پالایشگاه نفت","cat":"energy","m":500,"s":100,"d":5,"eff":"oil","v":20},
"power_plant":{"n":"⚡ نیروگاه","cat":"energy","m":450,"s":80,"d":4,"eff":"money","v":25},
"farm":{"n":"🌾 مزرعه","cat":"agri","m":250,"s":30,"d":2,"eff":"food","v":25},
"food_processing":{"n":"🍞 کارخانه غذا","cat":"agri","m":350,"s":50,"d":3,"eff":"food","v":30},
"hospital":{"n":"🏥 بیمارستان","cat":"social","m":300,"s":40,"d":3,"eff":"happiness","v":5},
"school":{"n":"🏫 مدرسه","cat":"social","m":250,"s":30,"d":2,"eff":"happiness","v":4},
"university":{"n":"🎓 دانشگاه","cat":"social","m":500,"s":70,"d":5,"eff":"research_bonus","v":10},
"water_system":{"n":"💧 سیستم آب","cat":"social","m":350,"s":50,"d":3,"eff":"water","v":40},
"propaganda":{"n":"📻 تبلیغات","cat":"politics","m":200,"s":20,"d":2,"eff":"happiness","v":3},
"conscription":{"n":"📋 خدمت اجباری","cat":"politics","m":500,"s":40,"d":4,"eff":"manpower","v":200},
"civil_reform":{"n":"📜 اصلاحات مدنی","cat":"politics","m":400,"s":30,"d":4,"eff":"happiness","v":8},
"fortress":{"n":"🏗️ استحکامات","cat":"military","m":400,"s":100,"d":4,"eff":"defense_bonus","v":25},
"intel_center":{"n":"🕵️ مرکز اطلاعات","cat":"military","m":400,"s":60,"d":3,"eff":"spy_bonus","v":10},
"army_base":{"n":"🏕️ پایگاه ارتش","cat":"military","m":300,"s":60,"d":3,"eff":"manpower","v":100},
"autobahn":{"n":"🛣️ اتوبان","cat":"transport","m":300,"s":60,"d":3,"eff":"speed","v":10},
"railway":{"n":"🚂 راه‌آهن","cat":"transport","m":350,"s":70,"d":3,"eff":"speed","v":12},
"port":{"n":"⚓ بندر","cat":"transport","m":450,"s":90,"d":5,"eff":"ship_bonus","v":10},
"naval_base":{"n":"⚓ پایگاه دریایی","cat":"transport","m":800,"s":150,"d":8,"eff":"naval","v":1},
}
SPECIAL_ITEMS = {
"force_exile":{"n":"🗳 اخراج اجباری"},"censor":{"n":"🤐 سانسور"},"expose":{"n":"🕵️ افشاگری"},
"seize_power":{"n":"👑 غصب قدرت"},"force_ally":{"n":"🤝 اتحاد اجباری"},"plunder":{"n":"💰 غارت"},
"war_speech":{"n":"📢 نطق جنگی"},"god_shield":{"n":"🛡 سپر جان"},"invisible":{"n":"👻 نامرئی"},
"double_attack":{"n":"⚡ دوبرابر حمله"},"revive":{"n":"🔄 برگشت فوری"},"lock_on":{"n":"🎯 قفل"},
"revenge":{"n":"💀 انتقام"},"war_storm":{"n":"🌪 طوفان"},"tsar_bomb":{"n":"💣 بمب تزار"},
"nuke_item":{"n":"☢️ بمب اتم"},"carpet_bomb":{"n":"🔥 بمباران قالی"},"bio_weapon":{"n":"☠️ بیولوژیک"},
"ballistic":{"n":"🚀 بالستیک"},
}
ITEM_FA = {"بمب تزار":"tsar_bomb","بمب اتم":"nuke_item","بمباران قالی":"carpet_bomb",
"سلاح بیولوژیک":"bio_weapon","موشک بالستیک":"ballistic","سپر جان":"god_shield",
"نامرئی":"invisible","دوبرابر حمله":"double_attack","برگشت فوری":"revive",
"قفل روی حریف":"lock_on","انتقام":"revenge","طوفان جنگی":"war_storm",
"اخراج اجباری":"force_exile","سانسور":"censor","افشاگری":"expose",
"غصب قدرت":"seize_power","اتحاد اجباری":"force_ally","غارت":"plunder","نطق جنگی":"war_speech"}
ATOMIC_STAGES = [{"n":"☢️ برنامه هسته‌ای","t":2,"m":500,"s":100,"o":0},
{"n":"⚛️ غنی‌سازی","t":2,"m":800,"s":150,"o":20},
{"n":"🔩 مونتاژ","t":1,"m":700,"s":150,"o":30}]
EVENTS = {"1939-09-01":"🇩🇪 حمله به لهستان","1939-09-03":"🇬🇧🇫🇷 اعلام جنگ",
"1940-05-10":"🇩🇪 حمله به فرانسه","1940-06-22":"🇫🇷 تسلیم فرانسه",
"1941-06-22":"🇩🇪 بارباروسا","1941-12-07":"🇯🇵 پرل هاربر",
"1942-08-23":"🔥 استالینگراد","1944-06-06":"🚢 D-Day",
"1945-05-08":"🏁 تسلیم آلمان","1945-08-06":"☢️ هیروشیما","1945-09-02":"🏁 تسلیم ژاپن"}
RANDOM_NEWS = ["🌧️ بارش شدید — {n} تلفات","🌊 سیل — {n} مجروح","🌍 زمین‌لرزه — {n} خسارت",
"❄️ موج سرما — {n} بی‌خانمان","🔥 آتش‌سوزی — {n} خسارت"]

def init_db():
    c = sqlite3.connect(DB_FILE)
    c.execute("CREATE TABLE IF NOT EXISTS players(user_id INTEGER PRIMARY KEY,country TEXT UNIQUE,gov TEXT,is_vip INTEGER DEFAULT 0)")
    c.execute("""CREATE TABLE IF NOT EXISTS states(user_id INTEGER PRIMARY KEY,turn INTEGER DEFAULT 1,
        game_date TEXT DEFAULT '1939-09-01',money REAL DEFAULT 0,food REAL DEFAULT 0,water REAL DEFAULT 0,
        steel REAL DEFAULT 0,oil REAL DEFAULT 0,coal REAL DEFAULT 0,manpower REAL DEFAULT 0,
        tax INTEGER DEFAULT 20,happiness INTEGER DEFAULT 70,surveillance INTEGER DEFAULT 20,
        protest INTEGER DEFAULT 0,protest_t INTEGER DEFAULT 0,suppress_cd INTEGER DEFAULT 0,
        war INTEGER DEFAULT 0,last_turn TEXT,atomic_stage INTEGER DEFAULT 0,atomic_t INTEGER DEFAULT 0,
        atomic_bombs INTEGER DEFAULT 0,soldiers INTEGER DEFAULT 0,dead INTEGER DEFAULT 0)""")
    c.execute("CREATE TABLE IF NOT EXISTS army(user_id INTEGER,category TEXT,model TEXT,count INTEGER DEFAULT 0,PRIMARY KEY(user_id,category,model))")
    c.execute("CREATE TABLE IF NOT EXISTS factories(user_id INTEGER,fkey TEXT,level INTEGER DEFAULT 1,PRIMARY KEY(user_id,fkey))")
    c.execute("CREATE TABLE IF NOT EXISTS research(user_id INTEGER,category TEXT,model TEXT,PRIMARY KEY(user_id,category,model))")
    c.execute("CREATE TABLE IF NOT EXISTS pq(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,category TEXT,model TEXT,qty INTEGER,turns INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS projq(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,pkey TEXT,turns INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS done_proj(user_id INTEGER,pkey TEXT,PRIMARY KEY(user_id,pkey))")
    c.execute("""CREATE TABLE IF NOT EXISTS wars(id INTEGER PRIMARY KEY AUTOINCREMENT,
        attacker TEXT,defender TEXT,atk_uid INTEGER,def_uid INTEGER,
        stage TEXT DEFAULT 'move',turns INTEGER DEFAULT 1,continued INTEGER DEFAULT 0)""")
    c.execute("CREATE TABLE IF NOT EXISTS allies(aid INTEGER,user_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS alliances(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,founder INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS nap(a INTEGER,b INTEGER,until_turn INTEGER,PRIMARY KEY(a,b))")
    c.execute("CREATE TABLE IF NOT EXISTS negs(id INTEGER PRIMARY KEY AUTOINCREMENT,from_id INTEGER,to_id INTEGER,kind TEXT,payload TEXT DEFAULT '',status TEXT DEFAULT 'pending')")
    c.execute("CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT,from_id INTEGER,to_id INTEGER,gr TEXT,ga INTEGER,wr TEXT,wa INTEGER,status TEXT DEFAULT 'pending')")
    c.execute("CREATE TABLE IF NOT EXISTS spies(id INTEGER PRIMARY KEY AUTOINCREMENT,from_id INTEGER,to_id INTEGER,turns INTEGER,status TEXT DEFAULT 'pending')")
    c.execute("CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item TEXT,payload TEXT,turns_left INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS news(id INTEGER PRIMARY KEY AUTOINCREMENT,turn INTEGER,cat TEXT,text TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS glob(k TEXT PRIMARY KEY,v TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS bombing(id INTEGER PRIMARY KEY AUTOINCREMENT,target_uid INTEGER,effect TEXT,turns INTEGER)")
    c.execute("INSERT OR IGNORE INTO glob(k,v) VALUES('turn','1')")
    c.execute("INSERT OR IGNORE INTO glob(k,v) VALUES('atomic_used','false')")
    c.commit(); c.close()

def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn
def gget(k, d=None):
    conn = db(); r = conn.execute("SELECT v FROM glob WHERE k=?", (k,)).fetchone(); conn.close()
    return r["v"] if r else d
def gset(k, v):
    conn = db(); conn.execute("INSERT OR REPLACE INTO glob(k,v) VALUES(?,?)", (k, str(v))); conn.commit(); conn.close()
def get_state(uid):
    conn = db()
    p = conn.execute("SELECT * FROM players WHERE user_id=?", (uid,)).fetchone()
    s = conn.execute("SELECT * FROM states WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    if not p or not s: return None
    r = dict(p); r.update(dict(s)); return r
def sset(uid, **kw):
    if not kw: return
    cols = ",".join(f"{k}=?" for k in kw)
    conn = db(); conn.execute(f"UPDATE states SET {cols} WHERE user_id=?", list(kw.values())+[uid])
    conn.commit(); conn.close()
def pset(uid, **kw):
    if not kw: return
    cols = ",".join(f"{k}=?" for k in kw)
    conn = db(); conn.execute(f"UPDATE players SET {cols} WHERE user_id=?", list(kw.values())+[uid])
    conn.commit(); conn.close()
def find_country(ck):
    conn = db(); r = conn.execute("SELECT user_id FROM players WHERE country=?", (ck,)).fetchone(); conn.close()
    return r["user_id"] if r else None
def all_players(exclude=None):
    conn = db()
    rows = conn.execute("SELECT user_id,country,is_vip FROM players").fetchall()
    conn.close()
    result = []
    for r in rows:
        if r["user_id"]==exclude: continue
        st = get_state(r["user_id"])
        if st and st.get("dead"): continue
        result.append({"uid":r["user_id"],"c":r["country"],"v":r["is_vip"]})
    return result
def taken():
    conn = db(); rows = conn.execute("SELECT country FROM players").fetchall(); conn.close()
    return {r["country"] for r in rows}
def is_admin(uid): return uid in ADMIN_IDS
def is_vip(uid):
    if is_admin(uid): return True
    conn = db(); r = conn.execute("SELECT is_vip FROM players WHERE user_id=?", (uid,)).fetchone(); conn.close()
    return bool(r and r["is_vip"])
def set_vip(uid, v=1):
    conn = db(); conn.execute("UPDATE players SET is_vip=? WHERE user_id=?", (v, uid)); conn.commit(); conn.close()
def get_army(uid):
    conn = db(); rows = conn.execute("SELECT * FROM army WHERE user_id=? AND count>0", (uid,)).fetchall(); conn.close()
    return [dict(r) for r in rows]
def add_army(uid, cat, model, cnt):
    conn = db()
    conn.execute("INSERT INTO army(user_id,category,model,count) VALUES(?,?,?,?) ON CONFLICT(user_id,category,model) DO UPDATE SET count=count+?", (uid, cat, model, cnt, cnt))
    conn.commit(); conn.close()
def get_res(uid, cat):
    conn = db(); rows = conn.execute("SELECT model FROM research WHERE user_id=? AND category=?", (uid, cat)).fetchall(); conn.close()
    return {r["model"] for r in rows}
def mark_res(uid, cat, model):
    conn = db(); conn.execute("INSERT OR IGNORE INTO research(user_id,category,model) VALUES(?,?,?)", (uid, cat, model)); conn.commit(); conn.close()
def get_fact(uid):
    conn = db(); rows = conn.execute("SELECT * FROM factories WHERE user_id=?", (uid,)).fetchall(); conn.close()
    return [dict(r) for r in rows]
def init_fact(uid):
    conn = db()
    for k in ["steel_mill","coal_mine","refinery","ammo_factory","farm"]:
        conn.execute("INSERT OR IGNORE INTO factories(user_id,fkey,level) VALUES(?,?,1)", (uid, k))
    conn.commit(); conn.close()
def get_pq(uid):
    conn = db(); rows = conn.execute("SELECT * FROM pq WHERE user_id=?", (uid,)).fetchall(); conn.close()
    return [dict(r) for r in rows]
def add_pq(uid, cat, model, qty, turns):
    conn = db(); conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)", (uid, cat, model, qty, turns)); conn.commit(); conn.close()
def get_projq(uid):
    conn = db(); rows = conn.execute("SELECT * FROM projq WHERE user_id=?", (uid,)).fetchall(); conn.close()
    return [dict(r) for r in rows]
def add_projq(uid, pk, turns):
    conn = db(); conn.execute("INSERT INTO projq(user_id,pkey,turns) VALUES(?,?,?)", (uid, pk, turns)); conn.commit(); conn.close()
def get_done_proj(uid):
    conn = db(); rows = conn.execute("SELECT pkey FROM done_proj WHERE user_id=?", (uid,)).fetchall(); conn.close()
    return {r["pkey"] for r in rows}
def mark_proj(uid, pk):
    conn = db(); conn.execute("INSERT OR IGNORE INTO done_proj(user_id,pkey) VALUES(?,?)", (uid, pk)); conn.commit(); conn.close()
def get_nap(a, b):
    conn = db(); r = conn.execute("SELECT until_turn FROM nap WHERE (a=? AND b=?) OR (a=? AND b=?)", (a,b,b,a)).fetchone(); conn.close()
    return r["until_turn"] if r else 0
def add_nap(a, b, until):
    conn = db(); conn.execute("INSERT OR REPLACE INTO nap(a,b,until_turn) VALUES(?,?,?)", (a,b,until)); conn.commit(); conn.close()
def get_user_alliance(uid):
    conn = db(); r = conn.execute("SELECT aid FROM allies WHERE user_id=?", (uid,)).fetchone(); conn.close()
    return r["aid"] if r else None
def get_alliance_members(aid):
    conn = db(); rows = conn.execute("SELECT user_id FROM allies WHERE aid=?", (aid,)).fetchall(); conn.close()
    return [r["user_id"] for r in rows]
def add_news(turn, cat, text):
    conn = db(); conn.execute("INSERT INTO news(turn,cat,text) VALUES(?,?,?)", (turn, cat, text)); conn.commit(); conn.close()
def has_effect(uid, effect):
    conn = db(); r = conn.execute("SELECT 1 FROM items WHERE user_id=? AND item=? AND turns_left>0", (uid, effect)).fetchone(); conn.close()
    return bool(r)
def add_effect(uid, effect, turns, payload=""):
    conn = db(); conn.execute("INSERT INTO items(user_id,item,payload,turns_left) VALUES(?,?,?,?)", (uid, effect, payload, turns)); conn.commit(); conn.close()
def fmt(n):
    try: return f"{int(n):,}"
    except: return str(n)
def parse_date(s):
    try: return datetime.strptime(s, "%Y-%m-%d")
    except: return datetime(1939,9,1)
def fmt_date(dt):
    m = ["ژانویه","فوریه","مارس","آپریل","مه","ژوئن","ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]
    return f"{dt.day} {m[dt.month-1]} {dt.year}"
def next_date(s): return (parse_date(s)+timedelta(days=1)).strftime("%Y-%m-%d")
def get_tree(ck, cat): return R.get(ck, {}).get(cat, [])

def calc_power(uid, mode="attack"):
    st = get_state(uid)
    if not st: return 0
    base = st.get("soldiers", 0) * 6
    for u in get_army(uid):
        pw = next((m[1] for m in get_tree(st["country"], u["category"]) if m[0]==u["model"]), 10)
        base += u["count"] * pw
    if mode == "defense":
        aa = sum(u["count"] * next((m[1] for m in get_tree(st["country"],"aa") if m[0]==u["model"]),10) for u in get_army(uid) if u["category"]=="aa")
        base += aa * 3
    if st["oil"] <= 0: base = int(base*0.6)
    if is_vip(uid): base *= 2
    if has_effect(uid, "double_attack"): base *= 2
    return int(base)

def calc_hap_delta(uid, st):
    d = 0
    tax = st.get("tax", 20)
    if tax > 40: d -= 7
    elif tax > 30: d -= 4
    elif tax > 25: d -= 2
    elif tax < 10: d += 4
    elif tax < 15: d += 2
    f = st.get("food", 0)
    if f < 100: d -= 5
    elif f < 300: d -= 2
    elif f > 3000: d += 2
    w = st.get("water", 0)
    if w < 50: d -= 4
    elif w > 1000: d += 1
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

def check_protest(uid, st):
    upd = {}
    if not st.get("protest"):
        hap = st["happiness"]
        if hap < 30:
            if hap>=25: ch=0.005
            elif hap>=20: ch=0.05
            elif hap>=15: ch=0.15
            elif hap>=10: ch=0.35
            elif hap>=5: ch=0.60
            else: ch=0.80
            if random.random() < ch:
                upd["protest"] = 1
                upd["protest_t"] = 3
                c = COUNTRIES[st["country"]]
                add_news(st["turn"], "protest", f"🔥 اعتراض در {c['n']} شروع شد!")
                add_news(st["turn"], "speech", f"📢 رهبر {c['n']} معترضان را وطن‌فروش خواند.")
    else:
        t = st.get("protest_t", 0) - 1
        if t <= 0:
            upd["protest"] = 0; upd["protest_t"] = 0
            upd["happiness"] = min(100, st["happiness"]+5)
        else:
            upd["protest_t"] = t
    return upd

def process_turn(uid):
    st = get_state(uid)
    if not st: return None
    c = COUNTRIES[st["country"]]
    mult = 2.0 if is_vip(uid) else 1.0
    upd = {}
    tm = st["tax"]/20.0
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
        t = b["turns"]-1
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
        nc = st["suppress_cd"]-1
        upd["suppress_cd"] = nc
        if nc==0: upd["happiness"] = max(0, upd.get("happiness", hap)-5)
    conn = db()
    for it in conn.execute("SELECT * FROM items WHERE turns_left>0").fetchall():
        t = it["turns_left"]-1
        if t <= 0: conn.execute("DELETE FROM items WHERE id=?", (it["id"],))
        else: conn.execute("UPDATE items SET turns_left=? WHERE id=?", (t, it["id"]))
    conn.commit(); conn.close()
    conn = db()
    for item in get_pq(uid):
        t = item["turns"]-1
        if t <= 0:
            add_army(uid, item["category"], item["model"], item["qty"])
            conn.execute("DELETE FROM pq WHERE id=?", (item["id"],))
        else:
            conn.execute("UPDATE pq SET turns=? WHERE id=?", (t, item["id"]))
    for p in get_projq(uid):
        t = p["turns"]-1
        if t <= 0:
            mark_proj(uid, p["pkey"])
            conn.execute("DELETE FROM projq WHERE id=?", (p["id"],))
        else:
            conn.execute("UPDATE projq SET turns=? WHERE id=?", (t, p["id"]))
    for s in conn.execute("SELECT * FROM spies WHERE from_id=? AND status='pending'", (uid,)).fetchall():
        t = s["turns"]-1
        if t <= 0:
            resolve_spy(uid, s["to_id"])
            conn.execute("UPDATE spies SET status='done' WHERE id=?", (s["id"],))
        else:
            conn.execute("UPDATE spies SET turns=? WHERE id=?", (t, s["id"]))
    conn.commit(); conn.close()
    if st.get("atomic_t", 0) > 0:
        t = st["atomic_t"]-1
        if t <= 0:
            ns = st.get("atomic_stage",0)+1
            upd["atomic_stage"] = ns; upd["atomic_t"] = 0
            if ns >= 3: upd["atomic_bombs"] = st.get("atomic_bombs",0)+1
        else:
            upd["atomic_t"] = t
    nd = next_date(st["game_date"])
    upd["game_date"] = nd; upd["turn"] = st["turn"]+1
    upd["last_turn"] = datetime.utcnow().isoformat()
    ev = []
    if nd in EVENTS:
        ev.append(EVENTS[nd])
        add_news(st["turn"], "hist", EVENTS[nd])
    sset(uid, **upd)
    return {"turn": st["turn"]+1, "date": nd, "ev": ev}

def resolve_spy(from_id, to_id):
    fs = get_state(from_id); ts = get_state(to_id)
    if not fs or not ts: return
    if to_id in ADMIN_IDS: return
    surv = ts.get("surveillance", 20)
    ch = 0.60 - (surv/100)*0.5
    if random.random() < ch:
        add_news(fs["turn"], "spy", f"🕵️ جاسوس {COUNTRIES[fs['country']]['n']} موفق بود")

def advance_wars():
    conn = db()
    wars = conn.execute("SELECT * FROM wars").fetchall()
    conn.close()
    for w in wars:
        au = w["atk_uid"]; du = w["def_uid"]
        ast = get_state(au); dst = get_state(du)
        if not ast or not dst or dst.get("dead"):
            conn = db(); conn.execute("DELETE FROM wars WHERE id=?", (w["id"],)); conn.commit(); conn.close(); continue
        t = w["turns"]-1
        stage = w["stage"]
        if stage == "move" and t <= 0:
            my = calc_power(au, "attack")
            en = calc_power(du, "defense")
            # اتحاد اجباری: هر عضو اتحاد مدافع اضافه می‌شه
            aid_d = get_user_alliance(du)
            if aid_d:
                for m in get_alliance_members(aid_d):
                    if m != du and m != au and m != dst["user_id"]:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            en += calc_power(m, "defense")
            aid_a = get_user_alliance(au)
            if aid_a:
                for m in get_alliance_members(aid_a):
                    if m != au and m != du:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            my += calc_power(m, "attack")
            add_news(int(gget("turn","1")), "battle",
                f"⚔️ نبرد: {COUNTRIES[w['attacker']]['n']} ({fmt(my)}) vs {COUNTRIES[w['defender']]['n']} ({fmt(en)})")
            if my > en:
                for u in get_army(au):
                    conn = db(); conn.execute("UPDATE army SET count=? WHERE id=?", (int(u["count"]*0.85), u["id"])); conn.commit(); conn.close()
                ds = get_state(du)
                if ds:
                    sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5, soldiers=int(ds["soldiers"]*0.5))
                conn = db(); conn.execute("UPDATE wars SET stage='resolve',turns=1 WHERE id=?", (w["id"],)); conn.commit(); conn.close()
                if calc_power(du, "defense") < my * 0.2:
                    asyncio.create_task(conquer_country(None, au, du))
            else:
                for u in get_army(au):
                    conn = db(); conn.execute("UPDATE army SET count=? WHERE id=?", (int(u["count"]*0.4), u["id"])); conn.commit(); conn.close()
                conn = db(); conn.execute("DELETE FROM wars WHERE id=?", (w["id"],)); conn.commit(); conn.close()
        elif stage == "resolve":
            ds = get_state(du)
            if ds:
                sset(du, money=ds["money"]*0.5, steel=ds["steel"]*0.5)
                for u in get_army(du):
                    conn = db(); conn.execute("UPDATE army SET count=? WHERE id=?", (int(u["count"]*0.5), u["id"])); conn.commit(); conn.close()
                asyncio.create_task(conquer_country(None, au, du))
            conn = db(); conn.execute("DELETE FROM wars WHERE id=?", (w["id"],)); conn.commit(); conn.close()

async def conquer_country(ctx, winner_uid, loser_uid):
    wst = get_state(winner_uid); lst = get_state(loser_uid)
    if not wst or not lst: return
    add_news(wst["turn"], "conquest",
        f"🏆 {COUNTRIES[wst['country']]['n']} کشور {COUNTRIES[lst['country']]['n']} را فتح کرد!")
    # انتقال ارتش
    for u in get_army(loser_uid):
        add_army(winner_uid, u["category"], u["model"], u["count"])
    # انتقال کارخونه‌ها (میانگین سطح)
    for f in get_fact(loser_uid):
        conn = db()
        ex = conn.execute("SELECT level FROM factories WHERE user_id=? AND fkey=?", (winner_uid, f["fkey"])).fetchone()
        if ex:
            new_lvl = min(5, (ex["level"] + f["level"]))
            conn.execute("UPDATE factories SET level=? WHERE user_id=? AND fkey=?", (new_lvl, winner_uid, f["fkey"]))
        else:
            conn.execute("INSERT INTO factories(user_id,fkey,level) VALUES(?,?,?)", (winner_uid, f["fkey"], f["level"]))
        conn.commit(); conn.close()
    # انتقال تحقیقات
    conn = db()
    rows = conn.execute("SELECT category,model FROM research WHERE user_id=?", (loser_uid,)).fetchall()
    for r in rows:
        conn.execute("INSERT OR IGNORE INTO research(user_id,category,model) VALUES(?,?,?)", (winner_uid, r["category"], r["model"]))
    conn.commit(); conn.close()
    # منابع (میانگین رضایت)
    sset(winner_uid,
         money=wst["money"]+lst["money"],
         steel=wst["steel"]+lst["steel"],
         oil=wst["oil"]+lst["oil"],
         food=wst["food"]+lst["food"],
         coal=wst["coal"]+lst["coal"],
         water=wst["water"]+lst["water"],
         manpower=wst["manpower"]+lst["manpower"],
         happiness=int((wst["happiness"]+lst["happiness"])/2))
    sset(loser_uid, dead=1)
    if ctx:
        try: await ctx.bot.send_message(winner_uid,
            f"🏆 *کشور {COUNTRIES[lst['country']]['n']} فتح شد!*\n\nسرنوشت رهبر؟",
            parse_mode="Markdown", reply_markup=kb_fate())
        except: pass
        try: await ctx.bot.send_message(loser_uid, f"💀 کشورت فتح شد! برای شروع مجدد: /start")
        except: pass

# کیبوردها
def kb_main(): return ReplyKeyboardMarkup([
    [KeyboardButton("💰 اقتصاد"),KeyboardButton("⚔️ ارتش")],
    [KeyboardButton("🔬 تحقیقات"),KeyboardButton("🏗️ پروژه‌ها")],
    [KeyboardButton("🏭 کارخونه‌ها"),KeyboardButton("🤝 دیپلماسی")],
    [KeyboardButton("📦 تجارت"),KeyboardButton("🎯 حمله")],
    [KeyboardButton("✈️ بمباران"),KeyboardButton("🕵️ جاسوسی")],
    [KeyboardButton("💵 مالیات"),KeyboardButton("🏛️ امور کشور")],
    [KeyboardButton("☢️ اتم"),KeyboardButton("📊 آمار کامل")]],resize_keyboard=True)
def kb_back(): return ReplyKeyboardMarkup([[KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_country():
    rows=[]; row=[]
    for k,c in COUNTRIES.items():
        ex_uid = find_country(k)
        if ex_uid:
            ex_st = get_state(ex_uid)
            if ex_st and not ex_st.get("dead"): continue
        row.append(KeyboardButton(f"{c['f']} {c['n']}"))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    return ReplyKeyboardMarkup(rows,resize_keyboard=True,one_time_keyboard=True)
def kb_gov(): return ReplyKeyboardMarkup([
    [KeyboardButton("👑 پادشاهی مطلقه"),KeyboardButton("👑 پادشاهی مشروطه")],
    [KeyboardButton("🗳️ جمهوری ریاستی"),KeyboardButton("🗳️ جمهوری پارلمانی")],
    [KeyboardButton("🚩 فاشیسم"),KeyboardButton("🚩 کمونیسم")],
    [KeyboardButton("⚙️ دیکتاتوری نظامی"),KeyboardButton("⚙️ دیکتاتوری شخصی")],
    [KeyboardButton("🕊️ دموکراسی لیبرال"),KeyboardButton("🕊️ دموکراسی اجتماعی")],
    [KeyboardButton("⚖️ تئوکراسی"),KeyboardButton("🚩 تک‌حزبی")]],resize_keyboard=True,one_time_keyboard=True)
def kb_army(): return ReplyKeyboardMarkup([
    [KeyboardButton("🪖 سرباز"),KeyboardButton("🛡️ تانک")],
    [KeyboardButton("✈️ جنگنده"),KeyboardButton("🚀 جت")],
    [KeyboardButton("🚢 کشتی"),KeyboardButton("🎯 موشک")],
    [KeyboardButton("💣 بمب‌افکن"),KeyboardButton("🛡️ پدافند")],
    [KeyboardButton("📋 خدمت اجباری")],[KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_research(): return ReplyKeyboardMarkup([
    [KeyboardButton("🔬🛡️ تانک"),KeyboardButton("🔬✈️ جنگنده")],
    [KeyboardButton("🔬🚀 جت"),KeyboardButton("🔬🚢 کشتی")],
    [KeyboardButton("🔬🎯 موشک"),KeyboardButton("🔬💣 بمب‌افکن")],
    [KeyboardButton("🔬🛡️ پدافند")],[KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_projects(): return ReplyKeyboardMarkup([
    [KeyboardButton("🏭 صنعت"),KeyboardButton("⚡ انرژی")],
    [KeyboardButton("🎖️ نظامی"),KeyboardButton("🏥 اجتماعی")],
    [KeyboardButton("🌾 کشاورزی"),KeyboardButton("📜 سیاسی")],
    [KeyboardButton("🛣️ حمل‌ونقل")],[KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_dip(): return ReplyKeyboardMarkup([
    [KeyboardButton("🤝 پیشنهاد اتحاد"),KeyboardButton("☮️ پیشنهاد صلح")],
    [KeyboardButton("⚔️ اعلام جنگ"),KeyboardButton("🤐 پیمان عدم تعرض")],
    [KeyboardButton("📜 بیانیه رسمی"),KeyboardButton("🚪 خروج از اتحاد")],
    [KeyboardButton("📨 درخواست‌های من")],[KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_trade(): return ReplyKeyboardMarkup([
    [KeyboardButton("💰 پول"),KeyboardButton("🍞 غذا")],
    [KeyboardButton("💧 آب"),KeyboardButton("⚙️ فولاد")],
    [KeyboardButton("🛢️ نفت"),KeyboardButton("🪨 زغال")],
    [KeyboardButton("👥 نیرو"),KeyboardButton("❌ هیچی")],
    [KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_internal(): return ReplyKeyboardMarkup([
    [KeyboardButton("📢 سخنرانی"),KeyboardButton("🚔 سرکوب")],
    [KeyboardButton("🕵️ نظارت بر مردم")],[KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_surv(): return ReplyKeyboardMarkup([
    [KeyboardButton("🕵️ نظارت +۱۰"),KeyboardButton("🕵️ نظارت -۱۰")],
    [KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_bomb(): return ReplyKeyboardMarkup([
    [KeyboardButton("🏭 بمباران کارخونه"),KeyboardButton("🔧 بمباران تجهیزات")],
    [KeyboardButton("💀 ترور فرمانده"),KeyboardButton("🛢️ بمباران پالایشگاه")],
    [KeyboardButton("🔙 منو")]],resize_keyboard=True)
def kb_fate(): return ReplyKeyboardMarkup([
    [KeyboardButton("🔴 اعدام"),KeyboardButton("🟢 بخشش")],
    [KeyboardButton("🔒 حبس")]],resize_keyboard=True)
def kb_targets(exclude):
    ps = all_players(exclude); rows=[]; row=[]
    for p in ps:
        c = COUNTRIES[p["c"]]
        row.append(KeyboardButton(f"{c['f']} {c['n']}"))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows,resize_keyboard=True)
def kb_models(ck, cat, uid):
    tree = get_tree(ck, cat); rows=[]; row=[]
    for item in tree:
        row.append(KeyboardButton(item[0]))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows,resize_keyboard=True)
def kb_fact(uid):
    f = get_fact(uid); rows=[]; row=[]
    for x in f:
        p = PROJECTS.get(x["fkey"],{})
        row.append(KeyboardButton(p.get("n",x["fkey"])))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows,resize_keyboard=True)

def render_dash(st):
    c = COUNTRIES[st["country"]]
    return (f"{c['f']} *{c['n']}* — {fmt_date(parse_date(st['game_date']))}\n"
        f"🔢 نوبت: {st['turn']} / {TOTAL_TURNS}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 {fmt(st['money'])}  🍞 {fmt(st['food'])}  ⚙️ {fmt(st['steel'])}\n"
        f"🛢️ {fmt(st['oil'])}  🪨 {fmt(st['coal'])}  👥 {fmt(st['manpower'])}\n"
        f"🪖 سرباز: {fmt(st['soldiers'])}\n"
        f"😊 {int(st['happiness'])}%  💵 {st['tax']}%")

def render_stats(uid):
    st = get_state(uid); c = COUNTRIES[st["country"]]
    lines = [f"{c['f']} *{c['n']}* — {fmt_date(parse_date(st['game_date']))}",
        f"🔢 {st['turn']}/{TOTAL_TURNS}",
        f"👑 {GOVS.get(st.get('gov'),('?',0))[0]}",
        "━━━━━━━━━━━━━━━━",
        f"💰{fmt(st['money'])} 🍞{fmt(st['food'])} 💧{fmt(st['water'])}",
        f"⚙️{fmt(st['steel'])} 🛢️{fmt(st['oil'])} 🪨{fmt(st['coal'])}",
        f"👥{fmt(st['manpower'])} 
    
# ═══════════════════════════════════════════════════════════════
#  💰 پرداخت — ادمین پرداخت نمی‌کنه
# ═══════════════════════════════════════════════════════════════
def pay(uid, money=0, steel=0, oil=0, food=0, coal=0, water=0, manpower=0):
    """پرداخت هزینه. اگه ادمین باشه، هیچی کم نمی‌شه."""
    if is_admin(uid): return True
    st = get_state(uid)
    if not st: return False
    if st["money"] < money or st["steel"] < steel or st["oil"] < oil:
        return False
    if st["food"] < food or st["coal"] < coal or st["water"] < water:
        return False
    if st["manpower"] < manpower: return False
    sset(uid, money=st["money"]-money, steel=st["steel"]-steel, oil=st["oil"]-oil,
         food=st["food"]-food, coal=st["coal"]-coal, water=st["water"]-water,
         manpower=st["manpower"]-manpower)
    return True


# ═══════════════════════════════════════════════════════════════
#  📨 ارسال پیام‌های معلق (جاسوسی، پیشنهاد، ...)
# ═══════════════════════════════════════════════════════════════
async def deliver_pending(ctx):
    """پیام‌های معلق جاسوسی رو به بازیکنان بفرست"""
    players = all_players()
    for p in players:
        uid = p["uid"]
        last_read = int(gget(f"spy_read_{uid}", "0") or 0)
        conn = db()
        rows = conn.execute(
            "SELECT * FROM news WHERE id>? AND cat IN (?, ?, ?) ORDER BY id",
            (last_read, f"spy_ok_{uid}", f"spy_fail_{uid}", f"battle_msg_{uid}")
        ).fetchall()
        conn.close()
        for r in rows:
            try:
                if r["cat"].startswith("spy_ok_"):
                    await ctx.bot.send_message(uid, f"✅ *جاسوسی موفق!*\n{r['text']}", parse_mode="Markdown")
                elif r["cat"].startswith("spy_fail_"):
                    await ctx.bot.send_message(uid, f"❌ *جاسوس لو رفت!*\n{r['text']}", parse_mode="Markdown")
                elif r["cat"].startswith("battle_msg_"):
                    await ctx.bot.send_message(uid, r["text"], parse_mode="Markdown", reply_markup=kb_main())
                last_read = r["id"]
            except: pass
        gset(f"spy_read_{uid}", str(last_read))


# ═══════════════════════════════════════════════════════════════
#  🎯 روتر اصلی
# ═══════════════════════════════════════════════════════════════
async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    uid = update.effective_user.id
    wait = ctx.user_data.get("wait")
    screen = ctx.user_data.get("screen", "menu")

    # ─── چک سانسور ───
    if has_effect(uid, "censored"):
        await update.message.reply_text("🤐 تو سانسور شدی! فعلاً نمی‌تونی حرف بزنی."); return

    # ─── پیام سازمان ملل ───
    if await on_un_message(update, ctx, text): return

    # ─── ورودی‌های انتظار ───
    if wait == "gov":
        await on_gov_pick(update, ctx); return
    if wait == "tax":
        try:
            v = int(text.replace("%","").strip())
            if not (0<=v<=50): raise ValueError
            sset(uid, tax=v); ctx.user_data["wait"]=None
            st = get_state(uid)
            await update.message.reply_text(f"✅ {v}%\n\n{render_dash(st)}", reply_markup=kb_main(), parse_mode="Markdown")
        except: await update.message.reply_text("❌ فرمت نامعتبر. عدد بین ۰ تا ۵۰ بفرست.")
        return
    if wait == "soldier":
        try:
            q = int(text)
            if q<=0: raise ValueError
        except: await update.message.reply_text("❌ عدد مثبت بفرست."); return
        if not pay(uid, money=50*q, manpower=q):
            await update.message.reply_text("❌ منابع کافی نداری!"); ctx.user_data["wait"]=None; return
        sset(uid, soldiers=get_state(uid).get("soldiers",0)+q)
        ctx.user_data["wait"]=None
        await update.message.reply_text(f"✅ {q} سرباز اضافه شد!", reply_markup=kb_main()); return
    if wait == "buy_amt" and ctx.user_data.get("buy_model"):
        try:
            q = int(text)
            if q<=0: raise ValueError
        except: await update.message.reply_text("❌ عدد مثبت."); return
        info = ctx.user_data["buy_model"]
        pm = info["power"]*20+100
        if not pay(uid, money=pm*q, steel=info["steel"]*q):
            await update.message.reply_text("❌ منابع کافی نداری!"); ctx.user_data["wait"]=None; return
        add_pq(uid, info["cat"], info["name"], q, info["build"])
        ctx.user_data["wait"]=None; ctx.user_data["buy_model"]=None
        await update.message.reply_text(f"✅ {q}× {info['name']} در صف ({info['build']} نوبت)", reply_markup=kb_main()); return
    if wait == "tr_amt":
        try:
            v = int(text)
            if v<=0: raise ValueError
        except: await update.message.reply_text("❌ عدد مثبت."); return
        step = ctx.user_data.get("tr_step")
        if step == "give_amt":
            ctx.user_data["tr_give_amt"] = v
            ctx.user_data["tr_step"] = "want"
            ctx.user_data["wait"] = None
            await update.message.reply_text("✅\n*مرحله ۳:* در ازای چی؟", reply_markup=kb_trade(), parse_mode="Markdown")
        elif step == "want_amt":
            ctx.user_data["tr_want_amt"] = v
            ctx.user_data["tr_step"] = "target"
            ctx.user_data["wait"] = "tr_target"
            await update.message.reply_text("🎯 طرف مقابل 👇", reply_markup=kb_targets(uid))
        return
    if wait == "statement":
        st = get_state(uid); c = COUNTRIES[st["country"]]
        msg = f"📜 بیانیه رسمی: {c['n']} {c['f']}\n━━━━━━━━━━━━━\n{text}\n━━━━━━━━━━━━━"
        try: await ctx.bot.send_message(NEWS_CH, msg)
        except: pass
        add_news(st["turn"],"statement",msg)
        ctx.user_data["wait"]=None
        await update.message.reply_text("✅ منتشر شد.", reply_markup=kb_main()); return
    if wait == "item_target" and ctx.user_data.get("use_item"):
        if text in CMAP:
            tk = CMAP[text]
            tu = find_country(tk)
            if tu:
                ik = ctx.user_data["use_item"]
                result = await apply_item(ctx, uid, ik, tu)
                await update.message.reply_text(result, reply_markup=kb_main())
                ctx.user_data["wait"] = None; ctx.user_data["use_item"] = None
                return

    # ─── پاسخ به درخواست دیپلماتیک ───
    if text.startswith("✅ قبول #"):
        try: nid = int(text.split("#")[1]); await on_neg_resp(update,ctx,nid,True); return
        except: pass
    if text.startswith("❌ رد #"):
        try: nid = int(text.split("#")[1]); await on_neg_resp(update,ctx,nid,False); return
        except: pass

    # ─── پاسخ به پیشنهاد تجاری ───
    if text.startswith("✅ قبول ") and not text.startswith("✅ قبول #"):
        try:
            tid = int(text.split(" ", 2)[2])
            await on_trade_resp(update, ctx, tid, True); return
        except: pass
    if text.startswith("❌ رد ") and not text.startswith("❌ رد #"):
        try:
            tid = int(text.split(" ", 2)[2])
            await on_trade_resp(update, ctx, tid, False); return
        except: pass

    # ─── عضویت ───
    if text == "عضو شدم ✅": await on_joined(update,ctx); return

    # ─── انتخاب کشور در context ───
    if text in CMAP:
        if wait == "dip_target": await on_dip_target(update,ctx); return
        if wait == "spy_target": await on_spy_target(update,ctx); return
        if wait == "atk_target": await on_attack_target(update,ctx); return
        if wait == "tr_target": await on_trade_target(update,ctx); return
        if wait == "bomb_target": await on_bomb_target(update,ctx); return
        if not get_state(uid) or get_state(uid).get("dead"):
            await on_country_pick(update,ctx); return

    # ─── دستورات ادمین ───
    if text.startswith("هدیه آیتم ") and is_admin(uid): await cmd_item(update,ctx); return
    if text.startswith("هدیه ") and is_admin(uid):
        p = text.split()
        if len(p)>=4 and p[2] in ["پول","غذا","آب","فولاد","نفت","زغال","نیرو","سرباز"]:
            await cmd_give(update,ctx); return
    if text.startswith("اطلاعات ") and is_admin(uid): await cmd_info(update,ctx); return
    if text.endswith(" ویژه") and is_admin(uid): await cmd_vip(update,ctx); return
    if text == "نوبت بعدی" and is_admin(uid): await cmd_next_turn(update,ctx); return
    if text == "لیست بازیکنان": await cmd_players(update,ctx); return
    if text == "پنل مدیریت" and is_admin(uid): await cmd_admin(update,ctx); return
    if text == "آیدی من": await cmd_myid(update,ctx); return
    if text in ITEM_FA and is_admin(uid):
        ik = ITEM_FA[text]
        ctx.user_data["use_item"] = ik
        ctx.user_data["wait"] = "item_target"
        await update.message.reply_text(f"🎁 {text}\n🎯 کشور هدف 👇", reply_markup=kb_targets(uid)); return

    # ─── اعدام/بخشش/حبس ───
    if text == "🔴 اعدام": await on_fate(update,ctx,"execute"); return
    if text == "🟢 بخشش": await on_fate(update,ctx,"forgive"); return
    if text == "🔒 حبس": await on_fate(update,ctx,"prison"); return

    # ─── بازی جدید / منو ───
    if text == "🎮 بازی جدید": await on_newgame(update,ctx); return
    if text == "🔙 منو":
        ctx.user_data["screen"]="menu"; ctx.user_data["wait"]=None
        await cmd_menu(update,ctx); return

    st = get_state(uid)
    if not st or st.get("dead"): return

    # ─── screen: کارخونه ───
    if screen == "fact":
        for f in get_fact(uid):
            p = PROJECTS.get(f["fkey"],{})
            if p.get("n") == text:
                lvl = f["level"]
                if lvl >= 5: await update.message.reply_text("🏆 حداکثر سطح."); return
                costs = {1:500,2:1200,3:2500,4:5000}
                cost = costs.get(lvl, 0)
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰"); return
                conn = db()
                conn.execute("UPDATE factories SET level=level+1 WHERE user_id=? AND fkey=?", (uid, f["fkey"]))
                conn.commit(); conn.close()
                await update.message.reply_text(f"✅ {text} → سطح {lvl+1}", reply_markup=kb_main()); return

    # ─── screen: خرید یا تحقیق مدل ───
    if screen.startswith("buy_") or screen.startswith("research_"):
        cat = screen.split("_",1)[1]
        tree = get_tree(st["country"], cat)
        researched = get_res(uid, cat)
        for i,item in enumerate(tree):
            name, power = item[0], item[1]
            if name == text:
                if screen.startswith("buy_"):
                    if i!=0 and name not in researched:
                        await update.message.reply_text(f"🔒 {name} تحقیق نشده."); return
                    ctx.user_data["buy_model"] = {"cat":cat,"name":name,"power":power,"steel":item[4],"build":item[3]}
                    ctx.user_data["wait"] = "buy_amt"
                    pm = power*20+100
                    await update.message.reply_text(
                        f"🛒 *{name}*\nقدرت {power}\n💰{pm} ⚙️{item[4]} ⏱️{item[3]} نوبت\n\nتعداد:",
                        reply_markup=kb_back(), parse_mode="Markdown")
                    return
                else:
                    if i==0: await update.message.reply_text("این از اول بازه."); return
                    if name in researched: await update.message.reply_text("قبلاً تحقیق شده."); return
                    cost = item[2]
                    if not pay(uid, money=cost):
                        await update.message.reply_text(f"❌ نیاز: {cost}💰"); return
                    mark_res(uid, cat, name)
                    await update.message.reply_text(f"✅ {name} تحقیق شد! قدرت {power}", reply_markup=kb_main()); return

    # ─── screen: پروژه ───
    if screen.startswith("proj_"):
        cat = screen.split("_",1)[1]
        for pk,p in PROJECTS.items():
            if p["cat"]==cat and p["n"]==text:
                if pk in get_done_proj(uid): await update.message.reply_text("قبلاً انجام شد."); return
                if any(q["pkey"]==pk for q in get_projq(uid)): await update.message.reply_text("در حال ساخت."); return
                if not pay(uid, money=p["m"], steel=p["s"]):
                    await update.message.reply_text("❌ منابع کافی نیست."); return
                add_projq(uid, pk, p["d"])
                await update.message.reply_text(f"✅ {p['n']} شروع شد ({p['d']} نوبت)", reply_markup=kb_main()); return

    # ─── منوها ───
    if text == "💰 اقتصاد": await on_eco(update,ctx); return
    if text == "💵 تغییر مالیات": await on_tax(update,ctx); return
    if text == "⚔️ ارتش": await on_army(update,ctx); return
    if text == "🪖 سرباز": await on_soldier(update,ctx); return
    if text == "🛡️ تانک": await on_army_cat(update,ctx,"tanks"); return
    if text == "✈️ جنگنده": await on_army_cat(update,ctx,"fighters"); return
    if text == "🚀 جت": await on_army_cat(update,ctx,"jets"); return
    if text == "🚢 کشتی": await on_army_cat(update,ctx,"ships"); return
    if text == "🎯 موشک": await on_army_cat(update,ctx,"missiles"); return
    if text == "💣 بمب‌افکن": await on_army_cat(update,ctx,"bombers"); return
    if text == "🛡️ پدافند": await on_army_cat(update,ctx,"aa"); return
    if text == "📋 خدمت اجباری":
        if not pay(uid, money=1000):
            await update.message.reply_text("❌ ۱۰۰۰💰 لازمه."); return
        st2 = get_state(uid)
        sset(uid, happiness=max(0, st2["happiness"]-15), manpower=st2["manpower"]+500)
        add_news(st2["turn"], "conscription", f"📋 خدمت اجباری در {COUNTRIES[st2['country']]['n']}")
        await update.message.reply_text("📋 خدمت اجباری!\n-۱۵ رضایت، +۵۰۰ نیرو", reply_markup=kb_main()); return
    if text == "🔬 تحقیقات": await on_research(update,ctx); return
    if text == "🔬🛡️ تانک": await on_research_cat(update,ctx,"tanks"); return
    if text == "🔬✈️ جنگنده": await on_research_cat(update,ctx,"fighters"); return
    if text == "🔬🚀 جت": await on_research_cat(update,ctx,"jets"); return
    if text == "🔬🚢 کشتی": await on_research_cat(update,ctx,"ships"); return
    if text == "🔬🎯 موشک": await on_research_cat(update,ctx,"missiles"); return
    if text == "🔬💣 بمب‌افکن": await on_research_cat(update,ctx,"bombers"); return
    if text == "🔬🛡️ پدافند": await on_research_cat(update,ctx,"aa"); return
    if text == "🏗️ پروژه‌ها": await on_projects(update,ctx); return
    if text == "🏭 صنعت": await on_projects_cat(update,ctx,"industry"); return
    if text == "⚡ انرژی": await on_projects_cat(update,ctx,"energy"); return
    if text == "🎖️ نظامی": await on_projects_cat(update,ctx,"military"); return
    if text == "🏥 اجتماعی": await on_projects_cat(update,ctx,"social"); return
    if text == "🌾 کشاورزی": await on_projects_cat(update,ctx,"agri"); return
    if text == "📜 سیاسی": await on_projects_cat(update,ctx,"politics"); return
    if text == "🛣️ حمل‌ونقل": await on_projects_cat(update,ctx,"transport"); return
    if text == "🏭 کارخونه‌ها": await on_fact(update,ctx); return
    if text == "🤝 دیپلماسی": await on_dip(update,ctx); return
    if text == "🤝 پیشنهاد اتحاد": await on_dip_action(update,ctx,"ally"); return
    if text == "☮️ پیشنهاد صلح": await on_dip_action(update,ctx,"peace"); return
    if text == "⚔️ اعلام جنگ": await on_dip_action(update,ctx,"war"); return
    if text == "🤐 پیمان عدم تعرض": await on_dip_action(update,ctx,"nap"); return
    if text == "📜 بیانیه رسمی": await on_statement(update,ctx); return
    if text == "🚪 خروج از اتحاد": await on_leave_alliance(update,ctx); return
    if text == "📨 درخواست‌های من": await on_negs(update,ctx); return
    if text == "📦 تجارت": await on_trade(update,ctx); return
    if text == "🎯 حمله": await on_attack(update,ctx); return
    if text == "✈️ بمباران": await on_bomb(update,ctx); return
    if text == "🏭 بمباران کارخونه": await on_bomb_type(update,ctx,"factory"); return
    if text == "🔧 بمباران تجهیزات": await on_bomb_type(update,ctx,"equip"); return
    if text == "💀 ترور فرمانده": await on_bomb_type(update,ctx,"assassin"); return
    if text == "🛢️ بمباران پالایشگاه": await on_bomb_type(update,ctx,"refinery"); return
    if text == "🕵️ جاسوسی": await on_spy(update,ctx); return
    if text == "🏛️ امور کشور": await on_internal(update,ctx); return
    if text == "📢 سخنرانی": await on_speech(update,ctx); return
    if text == "🚔 سرکوب": await on_suppress(update,ctx); return
    if text == "🕵️ نظارت بر مردم": await on_surv(update,ctx); return
    if text == "🕵️ نظارت +۱۰": await on_surv_change(update,ctx,10); return
    if text == "🕵️ نظارت -۱۰": await on_surv_change(update,ctx,-10); return
    if text == "📊 آمار کامل": await on_stats(update,ctx); return
    if text == "☢️ اتم": await on_atomic(update,ctx); return
    if text == "☢️ شروع مرحله": await on_atomic_start(update,ctx); return

    # ─── مراحل تجارت ───
    if ctx.user_data.get("tr_step") == "give": await on_trade_give(update,ctx); return
    if ctx.user_data.get("tr_step") == "want": await on_trade_want(update,ctx); return


# ═══════════════════════════════════════════════════════════════
#  ✅ پاسخ به پیشنهاد تجاری
# ═══════════════════════════════════════════════════════════════
async def on_trade_resp(update, ctx, tid, accept):
    uid = update.effective_user.id
    conn = db()
    r = conn.execute("SELECT * FROM trades WHERE id=? AND to_id=?", (tid, uid)).fetchone()
    if not r:
        conn.close(); await update.message.reply_text("❌ پیشنهاد پیدا نشد."); return
    r = dict(r)
    if r["status"] != "pending":
        conn.close(); await update.message.reply_text("❌ قبلاً پاسخ داده شده."); return
    conn.execute("UPDATE trades SET status=? WHERE id=?", ("accepted" if accept else "rejected", tid))
    conn.commit(); conn.close()
    if accept:
        from_id = r["from_id"]; to_id = r["to_id"]
        gr = r["gr"]; ga = r["ga"]; wr = r["wr"]; wa = r["wa"]
        fs = get_state(from_id); ts = get_state(to_id)
        if fs and ts:
            # کسر از فرستنده
            if gr != "nothing" and ga > 0:
                sset(from_id, **{gr: fs.get(gr, 0) - ga})
            # اضافه به گیرنده
            if gr != "nothing" and ga > 0:
                sset(to_id, **{gr: ts.get(gr, 0) + ga})
            # کسر از گیرنده
            if wr != "nothing" and wa > 0:
                sset(to_id, **{wr: ts.get(wr, 0) - wa})
            # اضافه به فرستنده
            if wr != "nothing" and wa > 0:
                sset(from_id, **{wr: fs.get(wr, 0) + wa})
    msg = "✅ قبول" if accept else "❌ رد"
    await update.message.reply_text(f"پیشنهاد تجاری: {msg}", reply_markup=kb_main())
    try: await ctx.bot.send_message(r["from_id"], f"📦 پیشنهاد تجاری تو: {msg}")
    except: pass


# ═══════════════════════════════════════════════════════════════
#  💰 درآمد هر ۵ ثانیه
# ═══════════════════════════════════════════════════════════════
async def fast_income(ctx):
    if gget("season_ended") == "true": return
    players = all_players()
    for p in players:
        try:
            st = get_state(p["uid"])
            if not st or st.get("dead"): continue
            c = COUNTRIES[st["country"]]
            mult = 2.0 if is_vip(p["uid"]) else 1.0
            tm = st["tax"]/20.0
            # اگه ادمین باشه، منابع رو افزایش می‌دیم بدون چک
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
#  🕐 نوبت خودکار — هر ۳۰ دقیقه
# ═══════════════════════════════════════════════════════════════
async def auto_turn(ctx):
    if gget("season_ended") == "true": return
    # ۱. پیشرفت جنگ‌ها
    advance_wars()
    # ۲. نوبت همه بازیکنان
    players = all_players()
    nt = int(gget("turn","1"))+1
    gset("turn", nt)
    for p in players:
        try:
            res = process_turn(p["uid"])
            if not res: continue
            t = f"📅 *نوبت {nt}* — {fmt_date(parse_date(res['date']))}\n"
            if res["ev"]:
                for e in res["ev"]: t += f"• {e}\n"
            await ctx.bot.send_message(p["uid"], t, parse_mode="Markdown", reply_markup=kb_main())
        except Exception as e:
            log.warning(f"turn {p['uid']}: {e}")
    # ۳. ارسال نتایج جاسوسی
    try: await deliver_pending(ctx)
    except Exception as e: log.warning(f"deliver: {e}")
    # ۴. اخبار سرگرمی
    if nt % 5 == 0:
        try:
            news = random.choice(RANDOM_NEWS)
            n = random.randint(10, 500)
            await ctx.bot.send_message(NEWS_CH, f"📰 {news.format(n=n)}")
        except: pass
    # ۵. رویدادهای اتم
    if nt == ATOMIC_UNLOCK:
        add_news(nt, "atomic", "☢️ پروژه اتمی باز شد برای آلمان و آمریکا!")
        try: await ctx.bot.send_message(NEWS_CH, "☢️ پروژه اتمی باز شد برای آلمان و آمریکا!")
        except: pass
    if nt == 2165:
        add_news(nt, "atomic", "☢️ اولین بمب اتم آماده استفاده است!")
    # ۶. سازمان ملل
    if nt % UN_INTERVAL == 0 and nt > 0:
        try: await start_un(ctx, nt)
        except Exception as e: log.warning(f"UN: {e}")
    # ۷. پایان سیزن
    if nt >= TOTAL_TURNS:
        gset("season_ended", "true")
        for p in players:
            try:
                await ctx.bot.send_message(p["uid"], "🏁 سیزن به پایان رسید!\nبرای شروع جدید /start بزن.")
            except: pass


# ═══════════════════════════════════════════════════════════════
#  🚀 main
# ═══════════════════════════════════════════════════════════════
def main():
    init_db()
    if "PASTE" in BOT_TOKEN:
        print("❌ توکن تنظیم نشده!")
        return
    try: keep_alive()
    except: pass

    app = Application.builder().token(BOT_TOKEN).base_url(BALE_API).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("players", cmd_players))
    app.add_handler(CommandHandler("next_turn", cmd_next_turn))
    app.add_handler(CommandHandler("admin", cmd_admin))

    # Router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # Jobs
    if app.job_queue:
        app.job_queue.run_repeating(auto_turn, interval=TURN_MINUTES*60, first=60)
        app.job_queue.run_repeating(fast_income, interval=5, first=10)
        print(f"⏰ نوبت خودکار هر {TURN_MINUTES} دقیقه")
        print(f"💰 درآمد هر ۵ ثانیه")

    print("🎖️ ربات جنگ جهانی دوم اجرا شد...")
    print(f"📅 شروع: 1939-09-01 | پایان: 1945-09-02")
    print(f"🔢 کل نوبت‌ها: {TOTAL_TURNS}")
    print(f"⚔️ حمله از نوبت {ATTACK_UNLOCK}")
    print(f"☢️ اتم از نوبت {ATOMIC_UNLOCK}")

    app.run_polling()


if __name__ == "__main__":
    main()
