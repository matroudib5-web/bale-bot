#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3, random, logging, asyncio
from datetime import datetime, timedelta
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton)
from telegram.ext import (Application, CommandHandler, MessageHandler,
    filters, ContextTypes)
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
CHANNELS = [
    {"u":"@Hitlerss1","l":"📢 کانال اول"},
    {"u":"@WORLDWAR21250","l":"📢 کانال دوم"},
]
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
"absolute_monarchy":("👑 پادشاهی مطلقه",-2),
"constitutional_monarchy":("👑 پادشاهی مشروطه",1),
"presidential_republic":("🗳️ جمهوری ریاستی",1),
"parliamentary_republic":("🗳️ جمهوری پارلمانی",2),
"fascist":("🚩 فاشیسم",-3),
"communism":("🚩 کمونیسم",-1),
"military_dictatorship":("⚙️ دیکتاتوری نظامی",-2),
"personal_dictatorship":("⚙️ دیکتاتوری شخصی",-3),
"liberal_democracy":("🕊️ دموکراسی لیبرال",2),
"social_democracy":("🕊️ دموکراسی اجتماعی",3),
"theocracy":("⚖️ تئوکراسی",-1),
"single_party":("🚩 تک‌حزبی",-2),
}
def M(n,p,c,b,s,o,d): return (n,p,c,b,s,o,d)
R = {}
R["germany"]={
"tanks":[M("Panzer I",5,50,1,20,0,"سبک"),M("Panzer II",8,100,1,40,0,"شناسایی"),M("Panzer III",12,200,2,80,5,"متوسط"),M("Panzer IV",18,350,2,140,10,"اصلی"),M("Tiger I",28,700,3,250,20,"سنگین")],
"fighters":[M("Ar 68",6,50,1,15,5,"آموزشی"),M("Bf 109E",10,100,1,30,10,"اصلی"),M("Bf 109G",15,200,2,60,20,"برتر"),M("Fw 190",20,350,2,100,30,"سنگین"),M("Ta 152",26,600,3,180,45,"پیشرفته")],
"jets":[M("He 178",15,200,2,50,30,"اولین"),M("Me 262",30,500,3,150,60,"افسانه"),M("He 162",24,400,3,100,45,"Volks"),M("Ho 229",34,700,4,200,70,"بال‌پرنده"),M("Arado 234",32,650,4,180,65,"جت‌بمب")],
"ships":[M("U-Boat VII",14,100,3,40,10,"زیردریایی"),M("Scharnhorst",20,250,4,100,20,"رزمناو"),M("Bismarck",28,450,5,180,30,"ناو"),M("Tirpitz",32,600,6,220,40,"ناو"),M("Graf Zeppelin",36,750,7,280,50,"ناو‌هواپیمابر")],
"missiles":[M("V-1",12,150,2,30,20,"کروز"),M("V-2",24,400,3,80,40,"بالستیک"),M("V-3",30,600,4,120,55,"چندمرحله"),M("A9",38,900,5,200,80,"قاره‌پیما"),M("Silbervogel",42,1200,6,300,100,"فضایی")],
"bombers":[M("Do 17",8,80,2,25,15,"سبک"),M("He 111",12,150,2,50,25,"متوسط"),M("Ju 88",16,250,3,80,35,"چندنقش"),M("He 177",22,400,4,130,50,"سنگین"),M("Ju 390",28,700,5,200,70,"قاره‌پیما")],
"aa":[M("Flak 30",10,500,2,50,0,"۲۰mm"),M("Flakvierling",18,1000,3,100,0,"چهارلول"),M("Flak 43",25,2000,4,200,0,"۳۷mm"),M("Flak 36/37",45,5000,6,500,0,"۸۸mm"),M("Flak 40",80,25000,15,2500,0,"۱۲۸mm")]}
R["uk"]={
"tanks":[M("Vickers VI",5,50,1,20,0,"سبک"),M("Matilda II",12,200,2,80,5,"پیاده"),M("Churchill",20,400,3,150,15,"سنگین"),M("Cromwell",24,550,3,180,25,"سریع"),M("Comet",28,750,4,220,35,"برتر")],
"fighters":[M("Gladiator",6,50,1,15,5,"دوباله"),M("Hurricane",10,100,1,30,10,"اصلی"),M("Spitfire",16,250,2,70,20,"افسانه"),M("Typhoon",22,400,3,110,30,"سنگین"),M("Tempest",26,600,3,150,40,"برتر")],
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
"tanks":[M("T-26",5,50,1,20,0,"سبک"),M("BT-7",9,120,1,45,5,"سریع"),M("T-34",20,350,2,130,20,"افسانه"),M("KV-1",26,500,3,180,25,"سنگین"),M("IS-2",32,750,4,250,40,"برتر")],
"fighters":[M("I-15",6,50,1,15,5,"دوباله"),M("Yak-1",10,100,1,30,10,"اصلی"),M("La-5",16,250,2,70,20,"برتر"),M("Yak-9",20,400,2,100,30,"چندکاره"),M("La-9",26,600,3,150,45,"نهایی")],
"jets":[M("MiG-9",22,400,3,100,45,"اولیه"),M("Yak-15",20,380,3,90,40,"سبک"),M("La-15",26,500,4,130,55,"برتر"),M("MiG-15",36,800,5,200,80,"افسانه"),M("Il-28",32,700,4,180,70,"جت‌بمب")],
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

CAT_N = {"tanks":"🛡️ تانک","fighters":"✈️ جنگنده","jets":"🚀 جت",
"ships":"🚢 کشتی/ناو","missiles":"🎯 موشک","bombers":"💣 بمب‌افکن","aa":"🛡️ پدافند"}

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

EVENTS = {"1939-09-01":"🇩🇪 آلمان به لهستان حمله کرد",
"1939-09-03":"🇬🇧🇫🇷 انگلیس و فرانسه اعلام جنگ کردند",
"1940-05-10":"🇩🇪 آلمان به فرانسه حمله کرد",
"1940-06-22":"🇫🇷 فرانسه تسلیم شد",
"1940-07-10":"✈️ نبرد بریتانیا آغاز شد",
"1941-06-22":"🇩🇪 عملیات بارباروسا",
"1941-12-07":"🇯🇵 حمله به پرل هاربر",
"1941-12-11":"🇺🇸 آمریکا وارد جنگ شد",
"1942-06-04":"🌊 نبرد میدوی",
"1942-08-23":"🔥 نبرد استالینگراد",
"1943-02-02":"🏆 پیروزی شوروی در استالینگراد",
"1944-06-06":"🚢 عملیات اورلرد — D-Day",
"1945-02-04":"🤝 کنفرانس یالتا",
"1945-04-30":"💀 خودکشی هیتلر",
"1945-05-08":"🏁 تسلیم آلمان",
"1945-08-06":"☢️ بمباران اتمی هیروشیما",
"1945-08-09":"☢️ بمباران اتمی ناکازاکی",
"1945-09-02":"🏁 تسلیم ژاپن"}

RANDOM_NEWS = [
"🌧️ بارش‌های سیل‌آسا دیروز در شمال اروپا {n} نفر را آواره کرد.",
"🌊 سیل ویرانگر در سواحل مدیترانه به {n} نفر خسارت وارد کرد.",
"🌍 زمین‌لرزه‌ای به بزرگی ۵.۲ ریشتر در مرزهای ایتالیا {n} نفر را مجروح کرد.",
"❄️ موج سرمای بی‌سابقه در شرق اروپا {n} نفر را بی‌خانمان کرد.",
"🔥 آتش‌سوزی گسترده در جنگل‌های کانادا تاکنون {n} هکتار را نابود کرده است.",
"☀️ موج گرمای شدید در جنوب اروپا {n} نفر را به کام مرگ کشاند.",
"⛈️ طوفان فصلی در سواحل ژاپن {n} نفر را مجروح کرد."]

def init_db():
    c = sqlite3.connect(DB_FILE)
    c.execute("""CREATE TABLE IF NOT EXISTS players(
        user_id INTEGER PRIMARY KEY, country TEXT UNIQUE,
        gov TEXT, is_vip INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS states(
        user_id INTEGER PRIMARY KEY, turn INTEGER DEFAULT 1,
        game_date TEXT DEFAULT '1939-09-01',
        money REAL DEFAULT 0, food REAL DEFAULT 0, water REAL DEFAULT 0,
        steel REAL DEFAULT 0, oil REAL DEFAULT 0, coal REAL DEFAULT 0,
        manpower REAL DEFAULT 0, tax INTEGER DEFAULT 20,
        happiness INTEGER DEFAULT 70, surveillance INTEGER DEFAULT 20,
        protest INTEGER DEFAULT 0, protest_t INTEGER DEFAULT 0,
        suppress_cd INTEGER DEFAULT 0, war INTEGER DEFAULT 0,
        last_turn TEXT, atomic_stage INTEGER DEFAULT 0,
        atomic_t INTEGER DEFAULT 0, atomic_bombs INTEGER DEFAULT 0,
        soldiers INTEGER DEFAULT 0, dead INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS army(
        user_id INTEGER, category TEXT, model TEXT, count INTEGER DEFAULT 0,
        PRIMARY KEY(user_id,category,model))""")
    c.execute("""CREATE TABLE IF NOT EXISTS factories(
        user_id INTEGER, fkey TEXT, level INTEGER DEFAULT 1,
        PRIMARY KEY(user_id,fkey))""")
    c.execute("""CREATE TABLE IF NOT EXISTS research(
        user_id INTEGER, category TEXT, model TEXT,
        PRIMARY KEY(user_id,category,model))""")
    c.execute("""CREATE TABLE IF NOT EXISTS pq(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        category TEXT, model TEXT, qty INTEGER, turns INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS projq(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        pkey TEXT, turns INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS done_proj(
        user_id INTEGER, pkey TEXT, PRIMARY KEY(user_id,pkey))""")
    c.execute("""CREATE TABLE IF NOT EXISTS wars(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attacker TEXT, defender TEXT,
        atk_uid INTEGER, def_uid INTEGER,
        stage TEXT DEFAULT 'move', turns INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS allies(
        aid INTEGER, user_id INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS alliances(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, founder INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS nap(
        a INTEGER, b INTEGER, until_turn INTEGER, PRIMARY KEY(a,b))""")
    c.execute("""CREATE TABLE IF NOT EXISTS negs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id INTEGER, to_id INTEGER, kind TEXT,
        payload TEXT DEFAULT '', status TEXT DEFAULT 'pending')""")
    c.execute("""CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id INTEGER, to_id INTEGER,
        gr TEXT, ga INTEGER, wr TEXT, wa INTEGER,
        status TEXT DEFAULT 'pending')""")
    c.execute("""CREATE TABLE IF NOT EXISTS spies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id INTEGER, to_id INTEGER, turns INTEGER,
        status TEXT DEFAULT 'pending')""")
    c.execute("""CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, item TEXT,
        payload TEXT DEFAULT '', turns_left INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS news(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turn INTEGER, cat TEXT, text TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS glob(
        k TEXT PRIMARY KEY, v TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bombing(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_uid INTEGER, effect TEXT, turns INTEGER)""")
    c.execute("INSERT OR IGNORE INTO glob(k,v) VALUES('turn','1')")
    c.execute("INSERT OR IGNORE INTO glob(k,v) VALUES('atomic_used','false')")
    c.execute("INSERT OR IGNORE INTO glob(k,v) VALUES('season_ended','false')")
    c.commit(); c.close()

def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def gget(k, d=None):
    conn = db(); r = conn.execute("SELECT v FROM glob WHERE k=?", (k,)).fetchone(); conn.close()
    return r["v"] if r else d

def gset(k, v):
    conn = db()
    conn.execute("INSERT OR REPLACE INTO glob(k,v) VALUES(?,?)", (k, str(v)))
    conn.commit(); conn.close()

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
    conn = db()
    conn.execute(f"UPDATE states SET {cols} WHERE user_id=?", list(kw.values())+[uid])
    conn.commit(); conn.close()

def pset(uid, **kw):
    if not kw: return
    cols = ",".join(f"{k}=?" for k in kw)
    conn = db()
    conn.execute(f"UPDATE players SET {cols} WHERE user_id=?", list(kw.values())+[uid])
    conn.commit(); conn.close()

def find_country(ck):
    conn = db()
    r = conn.execute("SELECT user_id FROM players WHERE country=?", (ck,)).fetchone()
    conn.close()
    return r["user_id"] if r else None

def all_players(exclude=None):
    conn = db()
    rows = conn.execute("SELECT user_id,country,is_vip FROM players").fetchall()
    conn.close()
    result = []
    for r in rows:
        if r["user_id"] == exclude: continue
        st = get_state(r["user_id"])
        if st and st.get("dead"): continue
        result.append({"uid":r["user_id"],"c":r["country"],"v":r["is_vip"]})
    return result

def taken():
    conn = db()
    rows = conn.execute("SELECT country FROM players").fetchall()
    conn.close()
    return {r["country"] for r in rows}

def is_admin(uid): return uid in ADMIN_IDS

def is_vip(uid):
    if is_admin(uid): return True
    conn = db()
    r = conn.execute("SELECT is_vip FROM players WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return bool(r and r["is_vip"])

def set_vip(uid, v=1):
    conn = db()
    conn.execute("UPDATE players SET is_vip=? WHERE user_id=?", (v, uid))
    conn.commit(); conn.close()

def get_army(uid):
    conn = db()
    rows = conn.execute("SELECT * FROM army WHERE user_id=? AND count>0", (uid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_army(uid, cat, model, cnt):
    conn = db()
    conn.execute("""INSERT INTO army(user_id,category,model,count) VALUES(?,?,?,?)
        ON CONFLICT(user_id,category,model) DO UPDATE SET count=count+?""",
        (uid, cat, model, cnt, cnt))
    conn.commit(); conn.close()

def get_res(uid, cat):
    conn = db()
    rows = conn.execute("SELECT model FROM research WHERE user_id=? AND category=?",
        (uid, cat)).fetchall()
    conn.close()
    return {r["model"] for r in rows}

def mark_res(uid, cat, model):
    conn = db()
    conn.execute("INSERT OR IGNORE INTO research(user_id,category,model) VALUES(?,?,?)",
        (uid, cat, model))
    conn.commit(); conn.close()

def get_fact(uid):
    conn = db()
    rows = conn.execute("SELECT * FROM factories WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def init_fact(uid):
    conn = db()
    for k in ["steel_mill","coal_mine","refinery","ammo_factory","farm"]:
        conn.execute("INSERT OR IGNORE INTO factories(user_id,fkey,level) VALUES(?,?,1)",
            (uid, k))
    conn.commit(); conn.close()

def get_pq(uid):
    conn = db()
    rows = conn.execute("SELECT * FROM pq WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_pq(uid, cat, model, qty, turns):
    conn = db()
    conn.execute("INSERT INTO pq(user_id,category,model,qty,turns) VALUES(?,?,?,?,?)",
        (uid, cat, model, qty, turns))
    conn.commit(); conn.close()

def get_projq(uid):
    conn = db()
    rows = conn.execute("SELECT * FROM projq WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_projq(uid, pk, turns):
    conn = db()
    conn.execute("INSERT INTO projq(user_id,pkey,turns) VALUES(?,?,?)", (uid, pk, turns))
    conn.commit(); conn.close()

def get_done_proj(uid):
    conn = db()
    rows = conn.execute("SELECT pkey FROM done_proj WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return {r["pkey"] for r in rows}

def mark_proj(uid, pk):
    conn = db()
    conn.execute("INSERT OR IGNORE INTO done_proj(user_id,pkey) VALUES(?,?)", (uid, pk))
    conn.commit(); conn.close()

def get_nap(a, b):
    conn = db()
    r = conn.execute("SELECT until_turn FROM nap WHERE (a=? AND b=?) OR (a=? AND b=?)",
        (a, b, b, a)).fetchone()
    conn.close()
    return r["until_turn"] if r else 0

def add_nap(a, b, until):
    conn = db()
    conn.execute("INSERT OR REPLACE INTO nap(a,b,until_turn) VALUES(?,?,?)", (a, b, until))
    conn.commit(); conn.close()

def cancel_nap(a, b):
    conn = db()
    conn.execute("DELETE FROM nap WHERE (a=? AND b=?) OR (a=? AND b=?)", (a, b, b, a))
    conn.commit(); conn.close()

def nap_active(a, b):
    until = get_nap(a, b)
    if not until: return False
    return int(gget("turn","1")) < until

def get_user_alliance(uid):
    conn = db()
    r = conn.execute("SELECT aid FROM allies WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r["aid"] if r else None

def get_alliance_members(aid):
    conn = db()
    rows = conn.execute("SELECT user_id FROM allies WHERE aid=?", (aid,)).fetchall()
    conn.close()
    return [r["user_id"] for r in rows]

def is_in_same_alliance(a, b):
    aa = get_user_alliance(a); bb = get_user_alliance(b)
    return aa and bb and aa == bb

def add_news(turn, cat, text):
    conn = db()
    conn.execute("INSERT INTO news(turn,cat,text) VALUES(?,?,?)", (turn, cat, text))
    conn.commit(); conn.close()

def has_effect(uid, effect):
    conn = db()
    r = conn.execute("SELECT 1 FROM items WHERE user_id=? AND item=? AND turns_left>0",
        (uid, effect)).fetchone()
    conn.close()
    return bool(r)

def add_effect(uid, effect, turns, payload=""):
    conn = db()
    conn.execute("INSERT INTO items(user_id,item,payload,turns_left) VALUES(?,?,?,?)",
        (uid, effect, payload, turns))
    conn.commit(); conn.close()

def fmt(n):
    try: return f"{int(n):,}"
    except: return str(n)

def parse_date(s):
    try: return datetime.strptime(s, "%Y-%m-%d")
    except: return datetime(1939,9,1)

def fmt_date(dt):
    m = ["ژانویه","فوریه","مارس","آپریل","مه","ژوئن",
         "ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]
    return f"{dt.day} {m[dt.month-1]} {dt.year}"

def next_date(s):
    return (parse_date(s)+timedelta(days=1)).strftime("%Y-%m-%d")

def get_tree(ck, cat): return R.get(ck, {}).get(cat, [])

def calc_power(uid, mode="attack"):
    st = get_state(uid)
    if not st: return 0
    base = st.get("soldiers", 0) * 6
    for u in get_army(uid):
        pw = next((m[1] for m in get_tree(st["country"], u["category"])
             if m[0]==u["model"]), 10)
        base += u["count"] * pw
    if mode == "defense":
        aa = sum(u["count"] * next((m[1] for m in get_tree(st["country"],"aa")
             if m[0]==u["model"]),10) for u in get_army(uid) if u["category"]=="aa")
        base += aa * 3
    if st["oil"] <= 0: base = int(base*0.6)
    if is_vip(uid): base *= 2
    if has_effect(uid, "double_attack"): base *= 2
    if has_effect(uid, "lock_on"): base = int(base * 1.3)
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
                add_news(st["turn"], "protest",
                    f"🔥 اعتراضات مردمی در {c['n']} برای اولین بار آغاز شد.")
                # فقط یه بار سخنرانی
                key = f"speech_protest_{uid}"
                if gget(key) != "done":
                    gset(key, "done")
                    sp = generate_speech(uid, "protest")
                    if sp: add_news(st["turn"], "speech", sp)
    else:
        t = st.get("protest_t", 0) - 1
        if t <= 0:
            upd["protest"] = 0; upd["protest_t"] = 0
            upd["happiness"] = min(100, st["happiness"]+5)
        else:
            upd["protest_t"] = t
    return upd

def generate_speech(uid, kind):
    st = get_state(uid)
    if not st: return None
    c = COUNTRIES[st["country"]]
    if kind == "war":
        return (f"📢 رهبر {c['n']} در سخنرانی امروز خود در برابر جمعیت گفت:\n\n"
                f"«ما در برابر تجاوز ایستاده‌ایم. هر وجب از خاک میهن با خون "
                f"فرزندان این سرزمین حفظ خواهد شد. دشمنان بدانند که ما تا آخرین "
                f"نفس مقاومت می‌کنیم و پیروزی از آن ملت ماست.»")
    if kind == "protest":
        return (f"📢 رهبر {c['n']} در واکنش به اعتراضات اخیر اعلام کرد:\n\n"
                f"«ما صدای مردم را می‌شنویم، اما هرج و مرج را تحمل نخواهیم کرد. "
                f"کشور نیازمند ثبات است و ما آن را تأمین خواهیم کرد. کسانی که "
                f"امنیت ملی را تهدید کنند، پاسخ سختی دریافت خواهند کرد.»")
    if kind == "suppress":
        return (f"📢 پس از سرکوب اعتراضات در {c['n']}، رهبر کشور در بیانیه‌ای اعلام کرد:\n\n"
                f"«نظم عمومی بازگردانده شده است. کسانی که قانون را زیر پا بگذارند، "
                f"با پاسخ قاطع دولت مواجه خواهند شد.»")
    if kind == "conquest":
        return (f"📢 {c['n']} در بیانیه‌ای رسمی پیروزی خود را اعلام کرد:\n\n"
                f"«پایتخت دشمن سقوط کرده است. ارتش ما بار دیگر عظمت خود را به "
                f"جهانیان نشان داد. ما برای صلح پایدار جنگیدیم.»")
    return None

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
        # ارسال به کانال
        try:
            pass  # توی auto_turn انجام می‌شه
        except: pass
    sset(uid, **upd)
    return {"turn": st["turn"]+1, "date": nd, "ev": ev}

def resolve_spy(from_id, to_id):
    fs = get_state(from_id); ts = get_state(to_id)
    if not fs or not ts: return
    if to_id in ADMIN_IDS:
        add_news(fs["turn"], f"spy_fail_{from_id}",
            f"جاسوس تو در کشور دشمن لو رفت و تمام اطلاعاتش فاش شد.")
        return
    surv = ts.get("surveillance", 20)
    ch = 0.60 - (surv/100)*0.5
    if random.random() < ch:
        text = (f"💰 پول: {fmt(ts['money'])}\n"
                f"⚙️ فولاد: {fmt(ts['steel'])}\n"
                f"🛢️ نفت: {fmt(ts['oil'])}\n"
                f"👥 نیرو: {fmt(ts['manpower'])}\n"
                f"🪖 سرباز: {fmt(ts['soldiers'])}")
        add_news(fs["turn"], f"spy_ok_{from_id}", text)
        add_news(fs["turn"], "spy",
            f"🕵️ جاسوس {COUNTRIES[fs['country']]['n']} اطلاعات ارزشمندی به دست آورد.")
    else:
        add_news(fs["turn"], f"spy_fail_{from_id}",
            f"جاسوس تو در کشور {COUNTRIES[ts['country']]['n']} لو رفت.")
        add_news(ts["turn"], f"spy_caught_{to_id}",
            f"🚨 جاسوسی از طرف {COUNTRIES[fs['country']]['n']} در کشورت کشف شد!")

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
            # اتحاد اجباری
            aid_d = get_user_alliance(du)
            if aid_d:
                for m in get_alliance_members(aid_d):
                    if m != du:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            en += calc_power(m, "defense")
                            # پیام به اعضا
                            try: pass
                            except: pass
            aid_a = get_user_alliance(au)
            if aid_a:
                for m in get_alliance_members(aid_a):
                    if m != au:
                        mst = get_state(m)
                        if mst and not mst.get("dead"):
                            my += calc_power(m, "attack")
            battle_msg = (f"⚔️ نبرد میان {COUNTRIES[w['attacker']]['n']} و "
                          f"{COUNTRIES[w['defender']]['n']}\n"
                          f"قدرت حمله: {fmt(my)} — قدرت دفاع: {fmt(en)}")
            add_news(int(gget("turn","1")), "battle", battle_msg)
            # پیام به کانال
            try:
                pass  # تو auto_turn ارسال می‌شه
            except: pass
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
                    f"🏆 {COUNTRIES[w['attacker']]['n']} در نبرد اولیه پیروز شد. "
                    f"نیروهای دشمن متلاشی شدند.")
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
                    f"💀 حمله {COUNTRIES[w['attacker']]['n']} شکست خورد و "
                    f"نیروهایش تلفات سنگین دادند.")
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

def conquer_country(ctx, winner_uid, loser_uid):
    wst = get_state(winner_uid); lst = get_state(loser_uid)
    if not wst or not lst: return
    add_news(wst["turn"], "conquest",
        f"🏆 ارتش {COUNTRIES[wst['country']]['n']} پایتخت "
        f"{COUNTRIES[lst['country']]['n']} را فتح کرد.")
    for u in get_army(loser_uid):
        add_army(winner_uid, u["category"], u["model"], u["count"])
    for f in get_fact(loser_uid):
        conn = db()
        ex = conn.execute("SELECT level FROM factories WHERE user_id=? AND fkey=?",
            (winner_uid, f["fkey"])).fetchone()
        if ex:
            new_lvl = min(5, ex["level"] + f["level"])
            conn.execute("UPDATE factories SET level=? WHERE user_id=? AND fkey=?",
                (new_lvl, winner_uid, f["fkey"]))
        else:
            conn.execute("INSERT INTO factories(user_id,fkey,level) VALUES(?,?,?)",
                (winner_uid, f["fkey"], f["level"]))
        conn.commit(); conn.close()
    conn = db()
    rows = conn.execute("SELECT category,model FROM research WHERE user_id=?",
        (loser_uid,)).fetchall()
    for r in rows:
        conn.execute("INSERT OR IGNORE INTO research(user_id,category,model) VALUES(?,?,?)",
            (winner_uid, r["category"], r["model"]))
    conn.commit(); conn.close()
    sset(winner_uid,
         money=wst["money"]+lst["money"],
         steel=wst["steel"]+lst["steel"],
         oil=wst["oil"]+lst["oil"],
         food=wst["food"]+lst["food"],
         coal=wst["coal"]+lst["coal"],
         water=wst["water"]+lst["water"],
         manpower=wst["manpower"]+lst["manpower"],
         soldiers=wst["soldiers"]+lst["soldiers"],
         happiness=int((wst["happiness"]+lst["happiness"])/2))
    sset(loser_uid, dead=1)
    key = f"speech_conquest_{winner_uid}"
    if gget(key) != "done":
        gset(key, "done")
        sp = generate_speech(winner_uid, "conquest")
        if sp: add_news(wst["turn"], "speech", sp)

def get_aa_power(uid):
    st = get_state(uid)
    if not st: return 0
    aa = sum(u["count"] * next((m[1] for m in get_tree(st["country"],"aa")
         if m[0]==u["model"]),10)
         for u in get_army(uid) if u["category"]=="aa")
    return aa

def do_bombing(from_uid, target_uid, kind, forces=100):
    """forces = تعداد نیروی هوایی فرستاده شده"""
    chances = {"factory":0.30,"equip":0.20,"assassin":0.05,"refinery":0.25}
    base = chances.get(kind, 0.20)
    # بستگی به نیرو
    force_mult = min(2.0, 0.5 + forces/200.0)
    base = base * force_mult
    aa = get_aa_power(target_uid)
    final = max(0, base - (aa/200))
    if random.random() < final:
        conn = db()
        if kind in ("factory","refinery"):
            # اثر به اندازه نیرو
            duration = min(5, max(1, forces//50))
            conn.execute("INSERT INTO bombing(target_uid,effect,turns) VALUES(?,?,?)",
                (target_uid, kind, duration))
            msg = f"✅ بمباران {kind} موفق ({int(final*100)}%). اثر تا {duration} نوبت."
        elif kind == "assassin":
            add_effect(target_uid, "no_attack", 1)
            msg = f"✅ ترور فرمانده موفق ({int(final*100)}%)."
        elif kind == "equip":
            tst = get_state(target_uid)
            if tst:
                sset(target_uid, soldiers=int(tst["soldiers"]*0.8))
            for u in get_army(target_uid):
                conn.execute("UPDATE army SET count=? WHERE id=?",
                    (int(u["count"]*0.8), u["id"]))
            msg = f"✅ بمباران تجهیزات موفق. ۲۰٪ تجهیزات دشمن نابود."
        else:
            msg = "✅ بمباران موفق."
        conn.commit(); conn.close()
        add_news(int(gget("turn","1")), "bomb",
            f"✈️ نیروی هوایی {COUNTRIES[get_state(from_uid)['country']]['n']} "
            f"مواضع دشمن را بمباران کرد.")
        return True, msg
    return False, f"❌ بمباران ناموفق ({int(final*100)}%)."

def use_atomic(uid, target_uid):
    st = get_state(uid); ts = get_state(target_uid)
    if not st or not ts: return "❌ خطا"
    if st.get("atomic_bombs", 0) <= 0:
        return "❌ بمب اتمی نداری."
    sset(uid, atomic_bombs=st["atomic_bombs"]-1)
    sset(target_uid, happiness=max(0, ts["happiness"]//2),
         soldiers=int(ts["soldiers"]*0.5))
    add_effect(target_uid, "no_attack", 3)
    gset("atomic_used", "true")
    add_news(st["turn"], "atomic",
        f"☢️ اولین بمب اتمی تاریخ توسط {COUNTRIES[st['country']]['n']} "
        f"بر فراز پایتخت {COUNTRIES[ts['country']]['n']} منفجر شد.")
    return f"☢️ بمب اتمی {COUNTRIES[ts['country']]['n']} را هدف گرفت."

async def apply_item_effect(ctx, uid, item_key, target_uid=None):
    st = get_state(uid)
    if not st: return "❌ خطا"
    c = COUNTRIES[st["country"]]
    result = "✅"
    # آیتم‌هایی که هدف نمی‌خوان
    if item_key in ("carpet_bomb", "war_speech", "war_storm", "revive"):
        if item_key == "carpet_bomb":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps:
                    sset(p["uid"], happiness=max(0, ps["happiness"]-10))
            result = "🔥 بمباران قالی — همه دشمنان آسیب دیدند."
        elif item_key == "war_speech":
            for p in all_players():
                if p["uid"] == uid: continue
                ps = get_state(p["uid"])
                if ps:
                    sset(p["uid"], money=max(0, ps["money"]*0.5))
            result = "📢 نطق جنگی — ۵۰٪ پول همه به تو رسید."
        elif item_key == "war_storm":
            result = "🌪 طوفان جنگی — همه حملات دشمن عقب رانده شد."
        elif item_key == "revive":
            add_effect(uid, "revive", 999)
            result = "🔄 محافظت مرگ فعال شد."
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
    elif item_key == "seize_power":
        add_effect(uid, "commander", 10)
        result = f"👑 {c['n']} ۱۰ نوبت فرمانده شد."
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
        conn.execute("INSERT OR IGNORE INTO allies(aid,user_id) VALUES(?,?)",
            (aid, target_uid))
        conn.commit(); conn.close()
        result = f"🤝 {COUNTRIES[get_state(target_uid)['country']]['n']} به اتحاد اضافه شد."
    elif item_key == "plunder" and target_uid:
        ts = get_state(target_uid)
        if ts:
            half = ts["money"] // 2
            sset(target_uid, money=ts["money"] - half)
            sset(uid, money=st["money"] + half)
            result = f"💰 {fmt(half)} پول از دشمن غارت شد."
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

def pay(uid, money=0, steel=0, oil=0, food=0, coal=0, water=0, manpower=0):
    if is_admin(uid): return True
    st = get_state(uid)
    if not st: return False
    if st["money"] < money or st["steel"] < steel or st["oil"] < oil: return False
    if st["food"] < food or st["coal"] < coal or st["water"] < water: return False
    if st["manpower"] < manpower: return False
    sset(uid,
         money=st["money"]-money, steel=st["steel"]-steel, oil=st["oil"]-oil,
         food=st["food"]-food, coal=st["coal"]-coal, water=st["water"]-water,
         manpower=st["manpower"]-manpower)
    return True

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
        f"👥{fmt(st['manpower'])} 🪖{fmt(st['soldiers'])}",
        f"😊{int(st['happiness'])}% 💵{st['tax']}% 🕵️{st.get('surveillance',20)}%"]
    for u in get_army(uid):
        lines.append(f"▪️ {u['model']}: {fmt(u['count'])}")
    return "\n".join(lines)
    
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
    for p in players:
        try:
            res = process_turn(p["uid"])
            if not res: continue
            t = f"📅 *نوبت {nt}* — {fmt_date(parse_date(res['date']))}\n"
            if res["ev"]:
                for e in res["ev"]:
                    t += f"• {e}\n"
                    # ارسال تاریخی به کانال
                    try:
                        await ctx.bot.send_message(NEWS_CH,
                            f"📰 *رویداد تاریخی — {res['date']}*\n\n{e}",
                            parse_mode="Markdown")
                    except: pass
            await ctx.bot.send_message(p["uid"], t,
                parse_mode="Markdown", reply_markup=kb_main())
        except Exception as e:
            log.warning(f"turn {p['uid']}: {e}")
    # ۳. جاسوسی
    try: await deliver_pending(ctx)
    except Exception as e: log.warning(f"deliver: {e}")
    # ۴. اخبار سرگرمی
    if nt % 5 == 0:
        try:
            news = random.choice(RANDOM_NEWS)
            n = random.randint(10, 500)
            await ctx.bot.send_message(NEWS_CH,
                f"📰 *خبر سرگرمی*\n\n{news.format(n=n)}",
                parse_mode="Markdown")
        except: pass
    # ۵. اتم
    if nt == ATOMIC_UNLOCK:
        add_news(nt, "atomic", "☢️ پروژه اتمی برای آلمان و آمریکا باز شد!")
        try:
            await ctx.bot.send_message(NEWS_CH,
                "☢️ *پروژه اتمی*\n\nپروژه منهتن امروز رسماً آغاز شد. "
                "آلمان و آمریکا وارد مرحله جدیدی از تحقیقات هسته‌ای شدند.",
                parse_mode="Markdown")
        except: pass
    # ۶. سازمان ملل
    if nt % UN_INTERVAL == 0 and nt > 0:
        try: await start_un(ctx, nt)
        except Exception as e: log.warning(f"UN: {e}")
    # ۷. پایان سیزن
    if nt >= TOTAL_TURNS:
        gset("season_ended", "true")
        for p in players:
            try:
                await ctx.bot.send_message(p["uid"],
                    "🏁 *سیزن به پایان رسید!*\n\nبرای شروع جدید /start بزن.",
                    parse_mode="Markdown")
            except: pass

# ═══════════════════════════════════════════════════════════════
#  🎯 روتر اصلی
# ═══════════════════════════════════════════════════════════════
async def on_text(update, ctx):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    uid = update.effective_user.id
    wait = ctx.user_data.get("wait")
    screen = ctx.user_data.get("screen", "menu")

    # سازمان ملل
    if await on_un_message(update, ctx, text): return

    # سانسور
    if has_effect(uid, "censored"):
        await update.message.reply_text("🤐 تو سانسور شدی! فعلاً نمی‌تونی حرف بزنی.")
        return

    # ورودی‌های انتظار
    if wait == "gov": await on_gov_pick(update, ctx); return
    if wait == "tax":
        try:
            v = int(text.replace("%","").strip())
            if not (0 <= v <= 50): raise ValueError
            sset(uid, tax=v); ctx.user_data["wait"]=None
            st = get_state(uid)
            await update.message.reply_text(
                f"✅ مالیات: {v}%\n\n{render_dash(st)}",
                reply_markup=kb_main(), parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ فرمت نامعتبر. عدد ۰ تا ۵۰ بفرست.")
        return
    if wait == "soldier":
        try:
            q = int(text)
            if q <= 0: raise ValueError
        except:
            await update.message.reply_text("❌ عدد مثبت بفرست."); return
        if not pay(uid, money=50*q, manpower=q):
            await update.message.reply_text("❌ منابع کافی نیست.")
            ctx.user_data["wait"]=None; return
        st = get_state(uid)
        sset(uid, soldiers=st.get("soldiers",0)+q)
        ctx.user_data["wait"]=None
        await update.message.reply_text(f"✅ {q} سرباز اضافه شد.", reply_markup=kb_main())
        return
    if wait == "buy_amt" and ctx.user_data.get("buy_model"):
        try:
            q = int(text)
            if q <= 0: raise ValueError
        except:
            await update.message.reply_text("❌ عدد مثبت."); return
        info = ctx.user_data["buy_model"]
        pm = info["power"]*20 + 100
        if not pay(uid, money=pm*q, steel=info["steel"]*q):
            await update.message.reply_text("❌ منابع کافی نیست.")
            ctx.user_data["wait"]=None; return
        add_pq(uid, info["cat"], info["name"], q, info["build"])
        ctx.user_data["wait"]=None; ctx.user_data["buy_model"]=None
        await update.message.reply_text(
            f"✅ {q}× {info['name']} در صف تولید ({info['build']} نوبت)",
            reply_markup=kb_main())
        return
    if wait == "tr_amt":
        try:
            v = int(text)
            if v <= 0: raise ValueError
        except:
            await update.message.reply_text("❌ عدد مثبت."); return
        step = ctx.user_data.get("tr_step")
        if step == "give_amt":
            ctx.user_data["tr_give_amt"] = v
            ctx.user_data["tr_step"] = "want"
            ctx.user_data["wait"] = None
            await update.message.reply_text("✅\n*مرحله ۳:* در ازای چی؟",
                reply_markup=kb_trade(), parse_mode="Markdown")
        elif step == "want_amt":
            ctx.user_data["tr_want_amt"] = v
            ctx.user_data["tr_step"] = "target"
            ctx.user_data["wait"] = "tr_target"
            await update.message.reply_text("🎯 طرف مقابل 👇", reply_markup=kb_targets(uid))
        return
    if wait == "statement":
        st = get_state(uid); c = COUNTRIES[st["country"]]
        msg = (f"📜 *بیانیه رسمی کشور {c['n']} {c['f']}*\n"
               f"━━━━━━━━━━━━━━━━\n{text}\n━━━━━━━━━━━━━━━━")
        try: await ctx.bot.send_message(NEWS_CH, msg, parse_mode="Markdown")
        except: pass
        add_news(st["turn"], "statement", msg)
        ctx.user_data["wait"]=None
        await update.message.reply_text("✅ بیانیه در کانال منتشر شد.",
            reply_markup=kb_main())
        return
    if wait == "item_target" and ctx.user_data.get("use_item"):
        if text in CMAP:
            tk = CMAP[text]
            tu = find_country(tk)
            if tu:
                ik = ctx.user_data["use_item"]
                result = await apply_item_effect(ctx, uid, ik, tu)
                await update.message.reply_text(result, reply_markup=kb_main())
                ctx.user_data["wait"]=None; ctx.user_data["use_item"]=None
                return

    # پاسخ به درخواست دیپلماتیک
    if text.startswith("✅ قبول #"):
        try:
            nid = int(text.split("#")[1])
            await on_neg_resp(update, ctx, nid, True); return
        except: pass
    if text.startswith("❌ رد #"):
        try:
            nid = int(text.split("#")[1])
            await on_neg_resp(update, ctx, nid, False); return
        except: pass
    # پاسخ به پیشنهاد تجاری
    if text.startswith("✅ قبول ") and not text.startswith("✅ قبول #"):
        try:
            tid = int(text.split(" ")[2])
            await on_trade_resp(update, ctx, tid, True); return
        except: pass
    if text.startswith("❌ رد ") and not text.startswith("❌ رد #"):
        try:
            tid = int(text.split(" ")[2])
            await on_trade_resp(update, ctx, tid, False); return
        except: pass

    # عضویت
    if text == "عضو شدم ✅":
        await on_joined(update, ctx); return

    # انتخاب کشور در context
    if text in CMAP:
        if wait == "dip_target": await on_dip_target(update, ctx); return
        if wait == "spy_target": await on_spy_target(update, ctx); return
        if wait == "atk_target": await on_attack_target(update, ctx); return
        if wait == "tr_target": await on_trade_target(update, ctx); return
        if wait == "bomb_target": await on_bomb_target(update, ctx); return
        if not get_state(uid) or get_state(uid).get("dead"):
            await on_country_pick(update, ctx); return

    # ادمین
    if text.startswith("هدیه آیتم ") and is_admin(uid): await cmd_item(update, ctx); return
    if text.startswith("هدیه ") and is_admin(uid):
        p = text.split()
        if len(p) >= 4 and p[2] in ["پول","غذا","آب","فولاد","نفت","زغال","نیرو","سرباز"]:
            await cmd_give(update, ctx); return
    if text.startswith("اطلاعات ") and is_admin(uid): await cmd_info(update, ctx); return
    if text.endswith(" ویژه") and is_admin(uid): await cmd_vip(update, ctx); return
    if text == "نوبت بعدی" and is_admin(uid): await cmd_next_turn(update, ctx); return
    if text == "لیست بازیکنان": await cmd_players(update, ctx); return
    if text == "پنل مدیریت" and is_admin(uid): await cmd_admin(update, ctx); return
    if text == "آیدی من": await cmd_myid(update, ctx); return
    if text in ITEM_FA and is_admin(uid):
        ik = ITEM_FA[text]
        # آیتم‌هایی که هدف نمی‌خوان
        if ik in ("carpet_bomb","war_speech","war_storm","revive"):
            result = await apply_item_effect(ctx, uid, ik)
            await update.message.reply_text(result, reply_markup=kb_main())
            return
        ctx.user_data["use_item"] = ik
        ctx.user_data["wait"] = "item_target"
        await update.message.reply_text(f"🎁 {text}\n🎯 کشور هدف 👇",
            reply_markup=kb_targets(uid))
        return

    # سرنوشت رهبر
    if text == "🔴 اعدام": await on_fate(update, ctx, "execute"); return
    if text == "🟢 بخشش": await on_fate(update, ctx, "forgive"); return
    if text == "🔒 حبس": await on_fate(update, ctx, "prison"); return

    # بازی جدید / منو
    if text == "🎮 بازی جدید": await on_newgame(update, ctx); return
    if text == "🔙 منو":
        ctx.user_data["screen"] = "menu"; ctx.user_data["wait"] = None
        await cmd_menu(update, ctx); return

    st = get_state(uid)
    if not st or st.get("dead"): return

    # screen: کارخونه
    if screen == "fact":
        for f in get_fact(uid):
            p = PROJECTS.get(f["fkey"], {})
            if p.get("n") == text:
                lvl = f["level"]
                if lvl >= 5:
                    await update.message.reply_text("🏆 حداکثر سطح."); return
                costs = {1:500, 2:1200, 3:2500, 4:5000}
                cost = costs.get(lvl, 0)
                if not pay(uid, money=cost):
                    await update.message.reply_text(f"❌ نیاز: {cost}💰"); return
                conn = db()
                conn.execute("UPDATE factories SET level=level+1 WHERE user_id=? AND fkey=?",
                    (uid, f["fkey"]))
                conn.commit(); conn.close()
                await update.message.reply_text(f"✅ {text} → سطح {lvl+1}",
                    reply_markup=kb_main()); return

    # screen: خرید یا تحقیق مدل
    if screen.startswith("buy_") or screen.startswith("research_"):
        cat = screen.split("_",1)[1]
        tree = get_tree(st["country"], cat)
        researched = get_res(uid, cat)
        for i, item in enumerate(tree):
            name, power = item[0], item[1]
            if name == text:
                if screen.startswith("buy_"):
                    if i != 0 and name not in researched:
                        await update.message.reply_text(f"🔒 {name} تحقیق نشده."); return
                    ctx.user_data["buy_model"] = {
                        "cat":cat, "name":name, "power":power,
                        "steel":item[4], "build":item[3]}
                    ctx.user_data["wait"] = "buy_amt"
                    pm = power*20 + 100
                    await update.message.reply_text(
                        f"🛒 *{name}*\nقدرت: {power}\n💰{pm} ⚙️{item[4]} "
                        f"⏱️{item[3]} نوبت\n\nتعداد:",
                        reply_markup=kb_back(), parse_mode="Markdown")
                    return
                else:
                    if i == 0:
                        await update.message.reply_text("این مدل از اول باز است."); return
                    if name in researched:
                        await update.message.reply_text("قبلاً تحقیق شده."); return
                    cost = item[2]
                    if not pay(uid, money=cost):
                        await update.message.reply_text(f"❌ نیاز: {cost}💰"); return
                    mark_res(uid, cat, name)
                    await update.message.reply_text(
                        f"✅ *{name}* تحقیق شد! قدرت {power}",
                        reply_markup=kb_main(), parse_mode="Markdown")
                    return

    # screen: پروژه
    if screen.startswith("proj_"):
        cat = screen.split("_",1)[1]
        for pk, p in PROJECTS.items():
            if p["cat"] == cat and p["n"] == text:
                if pk in get_done_proj(uid):
                    await update.message.reply_text("قبلاً انجام شده."); return
                if any(q["pkey"] == pk for q in get_projq(uid)):
                    await update.message.reply_text("در حال ساخت است."); return
                if not pay(uid, money=p["m"], steel=p["s"]):
                    await update.message.reply_text("❌ منابع کافی نیست."); return
                add_projq(uid, pk, p["d"])
                await update.message.reply_text(
                    f"✅ {p['n']} شروع شد ({p['d']} نوبت)",
                    reply_markup=kb_main())
                return

    # منوها
    if text == "💰 اقتصاد": await on_eco(update, ctx); return
    if text == "💵 تغییر مالیات": await on_tax(update, ctx); return
    if text == "⚔️ ارتش": await on_army(update, ctx); return
    if text == "🪖 سرباز": await on_soldier(update, ctx); return
    if text == "🛡️ تانک": await on_army_cat(update, ctx, "tanks"); return
    if text == "✈️ جنگنده": await on_army_cat(update, ctx, "fighters"); return
    if text == "🚀 جت": await on_army_cat(update, ctx, "jets"); return
    if text == "🚢 کشتی": await on_army_cat(update, ctx, "ships"); return
    if text == "🎯 موشک": await on_army_cat(update, ctx, "missiles"); return
    if text == "💣 بمب‌افکن": await on_army_cat(update, ctx, "bombers"); return
    if text == "🛡️ پدافند": await on_army_cat(update, ctx, "aa"); return
    if text == "📋 خدمت اجباری":
        if not pay(uid, money=1000):
            await update.message.reply_text("❌ ۱۰۰۰💰 لازمه."); return
        st2 = get_state(uid)
        sset(uid, happiness=max(0, st2["happiness"]-15), manpower=st2["manpower"]+500)
        msg = (f"📋 *خدمت اجباری در {COUNTRIES[st2['country']]['n']}*\n\n"
               f"دولت اعلام کرد تمام مردان بالای ۱۸ سال موظف به خدمت نظامی هستند.")
        add_news(st2["turn"], "conscription", msg)
        await post_to_channel(ctx, msg)
        await update.message.reply_text(
            "📋 خدمت اجباری فعال شد!\n-۱۵ رضایت، +۵۰۰ نیرو",
            reply_markup=kb_main())
        return
    if text == "🔬 تحقیقات": await on_research(update, ctx); return
    if text == "🔬🛡️ تانک": await on_research_cat(update, ctx, "tanks"); return
    if text == "🔬✈️ جنگنده": await on_research_cat(update, ctx, "fighters"); return
    if text == "🔬🚀 جت": await on_research_cat(update, ctx, "jets"); return
    if text == "🔬🚢 کشتی": await on_research_cat(update, ctx, "ships"); return
    if text == "🔬🎯 موشک": await on_research_cat(update, ctx, "missiles"); return
    if text == "🔬💣 بمب‌افکن": await on_research_cat(update, ctx, "bombers"); return
    if text == "🔬🛡️ پدافند": await on_research_cat(update, ctx, "aa"); return
    if text == "🏗️ پروژه‌ها": await on_projects(update, ctx); return
    if text == "🏭 صنعت": await on_projects_cat(update, ctx, "industry"); return
    if text == "⚡ انرژی": await on_projects_cat(update, ctx, "energy"); return
    if text == "🎖️ نظامی": await on_projects_cat(update, ctx, "military"); return
    if text == "🏥 اجتماعی": await on_projects_cat(update, ctx, "social"); return
    if text == "🌾 کشاورزی": await on_projects_cat(update, ctx, "agri"); return
    if text == "📜 سیاسی": await on_projects_cat(update, ctx, "politics"); return
    if text == "🛣️ حمل‌ونقل": await on_projects_cat(update, ctx, "transport"); return
    if text == "🏭 کارخونه‌ها": await on_fact(update, ctx); return
    if text == "🤝 دیپلماسی": await on_dip(update, ctx); return
    if text == "🤝 پیشنهاد اتحاد": await on_dip_action(update, ctx, "ally"); return
    if text == "☮️ پیشنهاد صلح": await on_dip_action(update, ctx, "peace"); return
    if text == "⚔️ اعلام جنگ": await on_dip_action(update, ctx, "war"); return
    if text == "🤐 پیمان عدم تعرض": await on_dip_action(update, ctx, "nap"); return
    if text == "📜 بیانیه رسمی": await on_statement(update, ctx); return
    if text == "🚪 خروج از اتحاد": await on_leave_alliance(update, ctx); return
    if text == "❌ لغو NAP": await on_cancel_nap(update, ctx); return
    if text == "📨 درخواست‌های من": await on_negs(update, ctx); return
    if text == "📦 تجارت": await on_trade(update, ctx); return
    if text == "🎯 حمله": await on_attack(update, ctx); return
    if text == "✈️ بمباران": await on_bomb(update, ctx); return
    if text == "🏭 بمباران کارخونه": await on_bomb_type(update, ctx, "factory"); return
    if text == "🔧 بمباران تجهیزات": await on_bomb_type(update, ctx, "equip"); return
    if text == "💀 ترور فرمانده": await on_bomb_type(update, ctx, "assassin"); return
    if text == "🛢️ بمباران پالایشگاه": await on_bomb_type(update, ctx, "refinery"); return
    if text == "🕵️ جاسوسی": await on_spy(update, ctx); return
    if text == "🏛️ امور کشور": await on_internal(update, ctx); return
    if text == "📢 سخنرانی": await on_speech(update, ctx); return
    if text == "🚔 سرکوب": await on_suppress(update, ctx); return
    if text == "🕵️ نظارت بر مردم": await on_surv(update, ctx); return
    if text == "🕵️ نظارت +۱۰": await on_surv_change(update, ctx, 10); return
    if text == "🕵️ نظارت -۱۰": await on_surv_change(update, ctx, -10); return
    if text == "📊 آمار کامل": await on_stats(update, ctx); return
    if text == "☢️ اتم": await on_atomic(update, ctx); return
    if text == "☢️ شروع مرحله": await on_atomic_start(update, ctx); return

    # مراحل تجارت
    if ctx.user_data.get("tr_step") == "give": await on_trade_give(update, ctx); return
    if ctx.user_data.get("tr_step") == "want": await on_trade_want(update, ctx); return

# ═══════════════════════════════════════════════════════════════
#  🚀 main
# ═══════════════════════════════════════════════════════════════
def main():
    init_db()
    if "PASTE" in BOT_TOKEN:
        print("❌ توکن تنظیم نشده!"); return
    try: keep_alive()
    except: pass

    app = Application.builder().token(BOT_TOKEN).base_url(BALE_API).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("players", cmd_players))
    app.add_handler(CommandHandler("next_turn", cmd_next_turn))
    app.add_handler(CommandHandler("admin", cmd_admin))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    if app.job_queue:
        app.job_queue.run_repeating(auto_turn, interval=TURN_MINUTES*60, first=60)
        app.job_queue.run_repeating(fast_income, interval=5, first=10)
        print(f"⏰ نوبت خودکار هر {TURN_MINUTES} دقیقه")
        print(f"💰 درآمد هر ۵ ثانیه")

    print("🎖️ ربات جنگ جهانی دوم اجرا شد...")
    print(f"🔢 کل نوبت‌ها: {TOTAL_TURNS}")
    print(f"⚔️ حمله از نوبت: {ATTACK_UNLOCK}")
    print(f"☢️ اتم از نوبت: {ATOMIC_UNLOCK}")

    app.run_polling()

# ═══════════════════════════════════════════════════════════════
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
    return await _old_on_text(update, ctx)

# ═══════════════════════════════════════════════════════════════
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
    await _old_auto_turn(ctx)

# ═══════════════════════════════════════════════════════════════
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
    return {"turn": st["turn"]+1, "date": nd, "ev": ev}

# ═══════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════
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
        reply_markup=kb_trade(), parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
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
    return await _old_on_text6(update, ctx)

# ═══════════════════════════════════════════════════════════════
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
    return await _old_on_text10(update, ctx)

# ═══════════════════════════════════════════════════════════════
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
    return await _old_on_text11(update, ctx)

# ═══════════════════════════════════════════════════════════════
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
        ], resize_keyboard=True), parse_mode="Markdown")

if __name__ == "__main__":
    main()
