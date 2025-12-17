#!/usr/bin/env python3
"""
Build a word index from song lyrics - V2.
Auto-searches for Spotify URIs so we just need artist + track names.
"""

import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path
from collections import defaultdict

WORDS_FILE = Path(__file__).parent / "words.json"
CACHE_FILE = Path(__file__).parent / "uri_cache.json"

# Just artist + track name - we'll find URIs automatically
SONGS = [
    # 80s classics
    ("Queen", "We Are The Champions"),
    ("Queen", "Bohemian Rhapsody"),
    ("Queen", "Don't Stop Me Now"),
    ("Queen", "Somebody To Love"),
    ("The Beatles", "All You Need Is Love"),
    ("The Beatles", "Hey Jude"),
    ("The Beatles", "Let It Be"),
    ("The Beatles", "Yesterday"),
    ("Michael Jackson", "Billie Jean"),
    ("Michael Jackson", "Beat It"),
    ("Michael Jackson", "Thriller"),
    ("Michael Jackson", "Bad"),
    ("Michael Jackson", "Man In The Mirror"),
    ("Prince", "Purple Rain"),
    ("Prince", "Kiss"),
    ("Prince", "When Doves Cry"),
    ("Whitney Houston", "I Wanna Dance With Somebody"),
    ("Whitney Houston", "I Will Always Love You"),
    ("Whitney Houston", "Greatest Love Of All"),
    ("Cyndi Lauper", "Girls Just Want To Have Fun"),
    ("Cyndi Lauper", "Time After Time"),
    ("Madonna", "Like A Prayer"),
    ("Madonna", "Material Girl"),
    ("Madonna", "Vogue"),
    ("Madonna", "Like A Virgin"),
    ("Bon Jovi", "Livin' On A Prayer"),
    ("Bon Jovi", "It's My Life"),
    ("Bon Jovi", "Wanted Dead Or Alive"),
    ("Journey", "Don't Stop Believin'"),
    ("Journey", "Open Arms"),
    ("a-ha", "Take On Me"),
    ("Survivor", "Eye Of The Tiger"),
    ("Toto", "Africa"),
    ("Europe", "The Final Countdown"),
    ("The Police", "Every Breath You Take"),
    ("Tears For Fears", "Everybody Wants To Rule The World"),
    ("Tears For Fears", "Shout"),
    ("Phil Collins", "In The Air Tonight"),
    ("Phil Collins", "Against All Odds"),
    ("Lionel Richie", "Hello"),
    ("Lionel Richie", "All Night Long"),
    ("Rick Astley", "Never Gonna Give You Up"),
    ("George Michael", "Careless Whisper"),
    ("George Michael", "Faith"),
    ("Wham!", "Wake Me Up Before You Go-Go"),
    ("Culture Club", "Karma Chameleon"),
    ("Duran Duran", "Hungry Like The Wolf"),
    ("Depeche Mode", "Enjoy The Silence"),
    ("Pet Shop Boys", "West End Girls"),
    ("Eurythmics", "Sweet Dreams"),
    ("Foreigner", "I Want To Know What Love Is"),
    ("REO Speedwagon", "Keep On Loving You"),
    ("Chicago", "Hard To Say I'm Sorry"),
    ("Air Supply", "All Out Of Love"),
    ("Starship", "We Built This City"),
    ("Starship", "Nothing's Gonna Stop Us Now"),
    ("Heart", "Alone"),
    ("Heart", "What About Love"),
    ("Def Leppard", "Pour Some Sugar On Me"),
    ("Van Halen", "Jump"),

    # 90s
    ("Nirvana", "Smells Like Teen Spirit"),
    ("Nirvana", "Come As You Are"),
    ("Pearl Jam", "Alive"),
    ("Pearl Jam", "Jeremy"),
    ("Red Hot Chili Peppers", "Under The Bridge"),
    ("Red Hot Chili Peppers", "Californication"),
    ("Green Day", "Basket Case"),
    ("Green Day", "American Idiot"),
    ("Oasis", "Wonderwall"),
    ("Oasis", "Don't Look Back In Anger"),
    ("Radiohead", "Creep"),
    ("R.E.M.", "Losing My Religion"),
    ("R.E.M.", "Everybody Hurts"),
    ("U2", "With Or Without You"),
    ("U2", "One"),
    ("U2", "Beautiful Day"),
    ("Alanis Morissette", "Ironic"),
    ("Alanis Morissette", "You Oughta Know"),
    ("No Doubt", "Don't Speak"),
    ("Backstreet Boys", "I Want It That Way"),
    ("Backstreet Boys", "Everybody"),
    ("NSYNC", "Bye Bye Bye"),
    ("NSYNC", "It's Gonna Be Me"),
    ("Britney Spears", "Baby One More Time"),
    ("Britney Spears", "Oops I Did It Again"),
    ("Britney Spears", "Toxic"),
    ("Spice Girls", "Wannabe"),
    ("TLC", "No Scrubs"),
    ("TLC", "Waterfalls"),
    ("Destiny's Child", "Say My Name"),
    ("Mariah Carey", "Fantasy"),
    ("Mariah Carey", "Always Be My Baby"),
    ("Mariah Carey", "We Belong Together"),
    ("Celine Dion", "My Heart Will Go On"),
    ("Celine Dion", "Because You Loved Me"),
    ("Shania Twain", "Man I Feel Like A Woman"),
    ("Shania Twain", "That Don't Impress Me Much"),
    ("Boyz II Men", "End Of The Road"),
    ("Boyz II Men", "I'll Make Love To You"),
    ("All-4-One", "I Swear"),
    ("Ace Of Base", "The Sign"),
    ("4 Non Blondes", "What's Up"),
    ("Chumbawamba", "Tubthumping"),
    ("Smash Mouth", "All Star"),
    ("Third Eye Blind", "Semi-Charmed Life"),
    ("Matchbox Twenty", "Push"),
    ("Goo Goo Dolls", "Iris"),
    ("Savage Garden", "Truly Madly Deeply"),
    ("Sixpence None The Richer", "Kiss Me"),
    ("Natalie Imbruglia", "Torn"),
    ("Des'ree", "You Gotta Be"),
    ("Seal", "Kiss From A Rose"),

    # 2000s
    ("Eminem", "Lose Yourself"),
    ("Eminem", "The Real Slim Shady"),
    ("Eminem", "Without Me"),
    ("Outkast", "Hey Ya"),
    ("Black Eyed Peas", "I Gotta Feeling"),
    ("Black Eyed Peas", "Where Is The Love"),
    ("Beyonce", "Crazy In Love"),
    ("Beyonce", "Single Ladies"),
    ("Beyonce", "Irreplaceable"),
    ("Beyonce", "Halo"),
    ("Rihanna", "Umbrella"),
    ("Rihanna", "Diamonds"),
    ("Rihanna", "We Found Love"),
    ("Lady Gaga", "Bad Romance"),
    ("Lady Gaga", "Poker Face"),
    ("Lady Gaga", "Born This Way"),
    ("Katy Perry", "Roar"),
    ("Katy Perry", "Firework"),
    ("Katy Perry", "Teenage Dream"),
    ("Katy Perry", "Hot N Cold"),
    ("Taylor Swift", "Shake It Off"),
    ("Taylor Swift", "Love Story"),
    ("Taylor Swift", "You Belong With Me"),
    ("Taylor Swift", "Blank Space"),
    ("Taylor Swift", "Bad Blood"),
    ("Adele", "Hello"),
    ("Adele", "Rolling In The Deep"),
    ("Adele", "Someone Like You"),
    ("Adele", "Set Fire To The Rain"),
    ("Amy Winehouse", "Rehab"),
    ("Coldplay", "Yellow"),
    ("Coldplay", "Viva La Vida"),
    ("Coldplay", "The Scientist"),
    ("Coldplay", "Fix You"),
    ("Coldplay", "Clocks"),
    ("The Killers", "Mr. Brightside"),
    ("The Killers", "Human"),
    ("Kings Of Leon", "Sex On Fire"),
    ("Kings Of Leon", "Use Somebody"),
    ("Snow Patrol", "Chasing Cars"),
    ("Keane", "Somewhere Only We Know"),
    ("Train", "Hey Soul Sister"),
    ("OneRepublic", "Apologize"),
    ("OneRepublic", "Counting Stars"),
    ("Maroon 5", "This Love"),
    ("Maroon 5", "She Will Be Loved"),
    ("Maroon 5", "Sugar"),
    ("Maroon 5", "Moves Like Jagger"),
    ("Bruno Mars", "Uptown Funk"),
    ("Bruno Mars", "Just The Way You Are"),
    ("Bruno Mars", "Grenade"),
    ("Bruno Mars", "24K Magic"),
    ("Jason Mraz", "I'm Yours"),
    ("John Legend", "All Of Me"),
    ("Meghan Trainor", "All About That Bass"),
    ("Pharrell Williams", "Happy"),
    ("Daft Punk", "Get Lucky"),
    ("LMFAO", "Party Rock Anthem"),
    ("Carly Rae Jepsen", "Call Me Maybe"),
    ("Gotye", "Somebody That I Used To Know"),
    ("Fun", "We Are Young"),
    ("Imagine Dragons", "Radioactive"),
    ("Imagine Dragons", "Believer"),
    ("Imagine Dragons", "Thunder"),

    # 2010s-2020s
    ("Ed Sheeran", "Shape Of You"),
    ("Ed Sheeran", "Thinking Out Loud"),
    ("Ed Sheeran", "Perfect"),
    ("The Weeknd", "Blinding Lights"),
    ("The Weeknd", "Starboy"),
    ("The Weeknd", "Can't Feel My Face"),
    ("Dua Lipa", "Don't Start Now"),
    ("Dua Lipa", "Levitating"),
    ("Dua Lipa", "New Rules"),
    ("Billie Eilish", "Bad Guy"),
    ("Billie Eilish", "Ocean Eyes"),
    ("Ariana Grande", "Thank U Next"),
    ("Ariana Grande", "7 Rings"),
    ("Ariana Grande", "Problem"),
    ("Post Malone", "Circles"),
    ("Post Malone", "Sunflower"),
    ("Post Malone", "Rockstar"),
    ("Drake", "Hotline Bling"),
    ("Drake", "God's Plan"),
    ("Drake", "One Dance"),
    ("Kendrick Lamar", "HUMBLE"),
    ("Lizzo", "Truth Hurts"),
    ("Lizzo", "Good As Hell"),
    ("Miley Cyrus", "Wrecking Ball"),
    ("Miley Cyrus", "Flowers"),
    ("Harry Styles", "Watermelon Sugar"),
    ("Harry Styles", "As It Was"),
    ("Olivia Rodrigo", "Drivers License"),
    ("Olivia Rodrigo", "Good 4 U"),
    ("Doja Cat", "Say So"),
    ("The Kid LAROI", "Stay"),
    ("Glass Animals", "Heat Waves"),
    ("Lil Nas X", "Old Town Road"),
    ("Lewis Capaldi", "Someone You Loved"),
    ("Sam Smith", "Stay With Me"),
    ("Hozier", "Take Me To Church"),
    ("Vance Joy", "Riptide"),
    ("Tones And I", "Dance Monkey"),
    ("Masked Wolf", "Astronaut In The Ocean"),

    # Classic Rock
    ("Led Zeppelin", "Stairway To Heaven"),
    ("Pink Floyd", "Comfortably Numb"),
    ("Pink Floyd", "Wish You Were Here"),
    ("Pink Floyd", "Another Brick In The Wall"),
    ("Eagles", "Hotel California"),
    ("Guns N' Roses", "Sweet Child O' Mine"),
    ("Guns N' Roses", "Welcome To The Jungle"),
    ("Guns N' Roses", "Paradise City"),
    ("AC/DC", "Back In Black"),
    ("AC/DC", "Highway To Hell"),
    ("AC/DC", "Thunderstruck"),
    ("Aerosmith", "I Don't Want To Miss A Thing"),
    ("Aerosmith", "Dream On"),
    ("Bon Jovi", "You Give Love A Bad Name"),
    ("Metallica", "Enter Sandman"),
    ("Metallica", "Nothing Else Matters"),
    ("Foo Fighters", "Everlong"),
    ("Foo Fighters", "Learn To Fly"),
    ("Linkin Park", "In The End"),
    ("Linkin Park", "Numb"),

    # R&B / Soul
    ("Louis Armstrong", "What A Wonderful World"),
    ("Aretha Franklin", "Respect"),
    ("Stevie Wonder", "Superstition"),
    ("Stevie Wonder", "Isn't She Lovely"),
    ("Marvin Gaye", "Let's Get It On"),
    ("Al Green", "Let's Stay Together"),
    ("Bill Withers", "Lean On Me"),
    ("Bill Withers", "Lovely Day"),
    ("Earth Wind Fire", "September"),
    ("Kool The Gang", "Celebration"),
    ("Usher", "Yeah"),
    ("Usher", "Burn"),
    ("Ne-Yo", "So Sick"),
    ("Chris Brown", "With You"),
    ("Jason Derulo", "Whatcha Say"),
    ("The Temptations", "My Girl"),

    # Hip-Hop / Rap
    ("Kanye West", "Stronger"),
    ("Kanye West", "Gold Digger"),
    ("Kanye West", "Heartless"),
    ("Kanye West", "All Of The Lights"),
    ("Kanye West", "Runaway"),
    ("Jay-Z", "Empire State Of Mind"),
    ("Jay-Z", "99 Problems"),
    ("Jay-Z", "Hard Knock Life"),
    ("Tupac", "California Love"),
    ("Tupac", "Changes"),
    ("Tupac", "Dear Mama"),
    ("The Notorious B.I.G.", "Juicy"),
    ("The Notorious B.I.G.", "Hypnotize"),
    ("The Notorious B.I.G.", "Big Poppa"),
    ("Snoop Dogg", "Drop It Like It's Hot"),
    ("Snoop Dogg", "Gin And Juice"),
    ("Dr. Dre", "Still D.R.E."),
    ("Dr. Dre", "Nuthin But A G Thang"),
    ("50 Cent", "In Da Club"),
    ("50 Cent", "Candy Shop"),
    ("Nelly", "Hot In Herre"),
    ("Nelly", "Dilemma"),
    ("Lil Wayne", "Lollipop"),
    ("Lil Wayne", "A Milli"),
    ("T.I.", "Whatever You Like"),
    ("T.I.", "Live Your Life"),
    ("Ludacris", "Get Back"),
    ("Ludacris", "Stand Up"),
    ("Missy Elliott", "Work It"),
    ("Missy Elliott", "Get Ur Freak On"),
    ("Lauryn Hill", "Doo Wop That Thing"),
    ("Lauryn Hill", "Everything Is Everything"),
    ("Nicki Minaj", "Super Bass"),
    ("Nicki Minaj", "Anaconda"),
    ("Cardi B", "Bodak Yellow"),
    ("Cardi B", "I Like It"),
    ("Megan Thee Stallion", "Savage"),
    ("Travis Scott", "Sicko Mode"),
    ("Travis Scott", "Goosebumps"),
    ("Tyler The Creator", "See You Again"),
    ("Childish Gambino", "This Is America"),
    ("Childish Gambino", "Redbone"),
    ("Chance The Rapper", "No Problem"),
    ("Mac Miller", "Self Care"),
    ("Juice WRLD", "Lucid Dreams"),
    ("XXXTentacion", "SAD!"),
    ("Lil Uzi Vert", "XO Tour Llif3"),
    ("21 Savage", "A Lot"),
    ("Migos", "Bad And Boujee"),
    ("Future", "Mask Off"),
    ("Young Thug", "Lifestyle"),
    ("A$AP Rocky", "Praise The Lord"),
    ("J. Cole", "Middle Child"),
    ("J. Cole", "No Role Modelz"),
    ("Logic", "1-800-273-8255"),

    # Country
    ("Johnny Cash", "Ring Of Fire"),
    ("Johnny Cash", "Folsom Prison Blues"),
    ("Johnny Cash", "Hurt"),
    ("Johnny Cash", "Walk The Line"),
    ("Dolly Parton", "Jolene"),
    ("Dolly Parton", "9 To 5"),
    ("Dolly Parton", "I Will Always Love You"),
    ("Willie Nelson", "On The Road Again"),
    ("Willie Nelson", "Blue Eyes Crying In The Rain"),
    ("Kenny Rogers", "The Gambler"),
    ("Kenny Rogers", "Islands In The Stream"),
    ("Glen Campbell", "Rhinestone Cowboy"),
    ("John Denver", "Take Me Home Country Roads"),
    ("John Denver", "Rocky Mountain High"),
    ("Garth Brooks", "Friends In Low Places"),
    ("Garth Brooks", "The Dance"),
    ("Tim McGraw", "Live Like You Were Dying"),
    ("Tim McGraw", "Humble And Kind"),
    ("Faith Hill", "Breathe"),
    ("Faith Hill", "This Kiss"),
    ("Shania Twain", "You're Still The One"),
    ("Carrie Underwood", "Before He Cheats"),
    ("Carrie Underwood", "Jesus Take The Wheel"),
    ("Taylor Swift", "Tim McGraw"),
    ("Taylor Swift", "Teardrops On My Guitar"),
    ("Keith Urban", "Somebody Like You"),
    ("Blake Shelton", "God Gave Me You"),
    ("Luke Bryan", "Country Girl"),
    ("Florida Georgia Line", "Cruise"),
    ("Zac Brown Band", "Chicken Fried"),
    ("Lady A", "Need You Now"),
    ("Little Big Town", "Pontoon"),
    ("Kacey Musgraves", "Follow Your Arrow"),
    ("Kacey Musgraves", "Rainbow"),
    ("Chris Stapleton", "Tennessee Whiskey"),
    ("Morgan Wallen", "Last Night"),
    ("Luke Combs", "Beautiful Crazy"),
    ("Kane Brown", "Heaven"),

    # Latin Pop / Reggaeton
    ("Shakira", "Hips Don't Lie"),
    ("Shakira", "Whenever Wherever"),
    ("Shakira", "Waka Waka"),
    ("Ricky Martin", "Livin La Vida Loca"),
    ("Ricky Martin", "She Bangs"),
    ("Enrique Iglesias", "Hero"),
    ("Enrique Iglesias", "Bailamos"),
    ("Enrique Iglesias", "Be With You"),
    ("Jennifer Lopez", "Jenny From The Block"),
    ("Jennifer Lopez", "On The Floor"),
    ("Jennifer Lopez", "Let's Get Loud"),
    ("Marc Anthony", "I Need To Know"),
    ("Marc Anthony", "You Sang To Me"),
    ("Pitbull", "Give Me Everything"),
    ("Pitbull", "Timber"),
    ("Pitbull", "International Love"),
    ("Daddy Yankee", "Gasolina"),
    ("Luis Fonsi", "Despacito"),
    ("J Balvin", "Mi Gente"),
    ("Bad Bunny", "Dakiti"),
    ("Bad Bunny", "Callaita"),
    ("Rosalia", "Malamente"),
    ("Maluma", "Felices Los 4"),
    ("Ozuna", "Taki Taki"),
    ("Camila Cabello", "Havana"),
    ("Camila Cabello", "Senorita"),
    ("Selena", "Dreaming Of You"),
    ("Selena", "Bidi Bidi Bom Bom"),
    ("Gloria Estefan", "Conga"),
    ("Gloria Estefan", "Rhythm Is Gonna Get You"),
    ("Carlos Santana", "Smooth"),
    ("Carlos Santana", "Maria Maria"),

    # Disco / Funk / Dance
    ("Bee Gees", "Stayin Alive"),
    ("Bee Gees", "How Deep Is Your Love"),
    ("Bee Gees", "Night Fever"),
    ("Donna Summer", "Hot Stuff"),
    ("Donna Summer", "I Feel Love"),
    ("Donna Summer", "Last Dance"),
    ("Gloria Gaynor", "I Will Survive"),
    ("KC And The Sunshine Band", "Get Down Tonight"),
    ("KC And The Sunshine Band", "Thats The Way I Like It"),
    ("Chic", "Le Freak"),
    ("Chic", "Good Times"),
    ("Sister Sledge", "We Are Family"),
    ("ABBA", "Dancing Queen"),
    ("ABBA", "Mamma Mia"),
    ("ABBA", "Take A Chance On Me"),
    ("ABBA", "Fernando"),
    ("ABBA", "Waterloo"),
    ("ABBA", "Gimme Gimme Gimme"),
    ("Blondie", "Heart Of Glass"),
    ("Blondie", "Call Me"),
    ("Village People", "YMCA"),
    ("Village People", "Macho Man"),
    ("Lipps Inc", "Funkytown"),
    ("Michael Sembello", "Maniac"),
    ("Irene Cara", "Flashdance What A Feeling"),
    ("Irene Cara", "Fame"),
    ("Kenny Loggins", "Footloose"),
    ("Kenny Loggins", "Danger Zone"),
    ("James Brown", "I Got You I Feel Good"),
    ("James Brown", "Get Up Offa That Thing"),
    ("Sly And The Family Stone", "Everyday People"),
    ("Parliament", "Flash Light"),
    ("Funkadelic", "One Nation Under A Groove"),
    ("Rick James", "Super Freak"),
    ("Prince", "1999"),
    ("Prince", "Lets Go Crazy"),
    ("Cameo", "Word Up"),
    ("Bobby Brown", "Every Little Step"),
    ("New Edition", "Candy Girl"),
    ("Bell Biv DeVoe", "Poison"),
    ("C+C Music Factory", "Gonna Make You Sweat"),
    ("Deee-Lite", "Groove Is In The Heart"),
    ("Technotronic", "Pump Up The Jam"),
    ("Snap", "The Power"),
    ("Haddaway", "What Is Love"),
    ("Corona", "Rhythm Of The Night"),
    ("La Bouche", "Be My Lover"),
    ("Real McCoy", "Another Night"),
    ("Ace Of Base", "All That She Wants"),
    ("Aqua", "Barbie Girl"),
    ("Vengaboys", "We Like To Party"),
    ("Eiffel 65", "Blue"),
    ("Crazy Town", "Butterfly"),

    # Indie / Alternative
    ("Arctic Monkeys", "Do I Wanna Know"),
    ("Arctic Monkeys", "I Bet You Look Good On The Dancefloor"),
    ("Arctic Monkeys", "505"),
    ("Tame Impala", "The Less I Know The Better"),
    ("Tame Impala", "Let It Happen"),
    ("MGMT", "Kids"),
    ("MGMT", "Electric Feel"),
    ("Foster The People", "Pumped Up Kicks"),
    ("Vampire Weekend", "A-Punk"),
    ("Vampire Weekend", "Oxford Comma"),
    ("The Strokes", "Last Nite"),
    ("The Strokes", "Reptilia"),
    ("Franz Ferdinand", "Take Me Out"),
    ("The White Stripes", "Seven Nation Army"),
    ("The Black Keys", "Lonely Boy"),
    ("The Black Keys", "Tighten Up"),
    ("Cage The Elephant", "Ain't No Rest For The Wicked"),
    ("Cage The Elephant", "Trouble"),
    ("Two Door Cinema Club", "What You Know"),
    ("Passion Pit", "Sleepyhead"),
    ("Walk The Moon", "Shut Up And Dance"),
    ("Bastille", "Pompeii"),
    ("Hozier", "Take Me To Church"),
    ("Mumford And Sons", "Little Lion Man"),
    ("Mumford And Sons", "I Will Wait"),
    ("The Lumineers", "Ho Hey"),
    ("Of Monsters And Men", "Little Talks"),
    ("Florence And The Machine", "Dog Days Are Over"),
    ("Florence And The Machine", "Shake It Off"),
    ("Lorde", "Royals"),
    ("Lorde", "Green Light"),
    ("CHVRCHES", "The Mother We Share"),
    ("Phoebe Bridgers", "Motion Sickness"),
    ("Mitski", "Your Best American Girl"),
    ("Bon Iver", "Skinny Love"),
    ("Fleet Foxes", "White Winter Hymnal"),
    ("Arcade Fire", "Wake Up"),
    ("Arcade Fire", "The Suburbs"),
    ("Modest Mouse", "Float On"),
    ("Death Cab For Cutie", "I Will Follow You Into The Dark"),
    ("Neutral Milk Hotel", "In The Aeroplane Over The Sea"),
    ("The Smiths", "There Is A Light That Never Goes Out"),
    ("The Cure", "Just Like Heaven"),
    ("The Cure", "Friday Im In Love"),
    ("Joy Division", "Love Will Tear Us Apart"),
    ("New Order", "Blue Monday"),
    ("Talking Heads", "Psycho Killer"),
    ("Talking Heads", "Once In A Lifetime"),
    ("Pixies", "Where Is My Mind"),
    ("Sonic Youth", "Teen Age Riot"),
    ("Pavement", "Cut Your Hair"),
    ("Weezer", "Buddy Holly"),
    ("Weezer", "Say It Ain't So"),
    ("Blink-182", "All The Small Things"),
    ("Blink-182", "I Miss You"),
    ("Sum 41", "Fat Lip"),
    ("Good Charlotte", "Lifestyles Of The Rich And Famous"),
    ("My Chemical Romance", "Welcome To The Black Parade"),
    ("My Chemical Romance", "Helena"),
    ("Fall Out Boy", "Sugar We're Goin Down"),
    ("Fall Out Boy", "Thnks Fr Th Mmrs"),
    ("Panic At The Disco", "I Write Sins Not Tragedies"),
    ("Panic At The Disco", "High Hopes"),
    ("Paramore", "Misery Business"),
    ("Paramore", "Decode"),
    ("Twenty One Pilots", "Stressed Out"),
    ("Twenty One Pilots", "Heathens"),
    ("Imagine Dragons", "Demons"),
    ("The 1975", "Somebody Else"),
    ("The 1975", "Chocolate"),
    ("Glass Animals", "Gooey"),
    ("alt-J", "Breezeblocks"),
    ("Portugal The Man", "Feel It Still"),
    ("Vampire Weekend", "Sunflower"),
    ("Gorillaz", "Feel Good Inc"),
    ("Gorillaz", "Clint Eastwood"),

    # Electronic / EDM
    ("Daft Punk", "Around The World"),
    ("Daft Punk", "One More Time"),
    ("Daft Punk", "Harder Better Faster Stronger"),
    ("Avicii", "Wake Me Up"),
    ("Avicii", "Levels"),
    ("Avicii", "Hey Brother"),
    ("Calvin Harris", "Feel So Close"),
    ("Calvin Harris", "Summer"),
    ("Calvin Harris", "This Is What You Came For"),
    ("David Guetta", "Titanium"),
    ("David Guetta", "When Love Takes Over"),
    ("Swedish House Mafia", "Don't You Worry Child"),
    ("Tiesto", "Red Lights"),
    ("Deadmau5", "Ghosts N Stuff"),
    ("Skrillex", "Bangarang"),
    ("Marshmello", "Happier"),
    ("Marshmello", "Alone"),
    ("Kygo", "Firestone"),
    ("Kygo", "It Ain't Me"),
    ("Zedd", "Clarity"),
    ("Zedd", "Stay"),
    ("The Chainsmokers", "Closer"),
    ("The Chainsmokers", "Don't Let Me Down"),
    ("Major Lazer", "Lean On"),
    ("DJ Snake", "Turn Down For What"),
    ("Diplo", "Revolution"),
    ("Martin Garrix", "Animals"),
    ("Alan Walker", "Faded"),
    ("Alan Walker", "Alone"),
    ("Kygo", "Stole The Show"),
    ("Flume", "Never Be Like You"),
    ("ODESZA", "A Moment Apart"),
    ("Disclosure", "Latch"),
    ("Clean Bandit", "Rather Be"),
    ("Clean Bandit", "Rockabye"),
    ("Rudimental", "Feel The Love"),
    ("Duke Dumont", "Ocean Drive"),
    ("Robin Schulz", "Sugar"),
    ("Sigala", "Sweet Lovin"),
    ("Jonas Blue", "Fast Car"),

    # 80s New Wave / Synthpop (more)
    ("Soft Cell", "Tainted Love"),
    ("Human League", "Don't You Want Me"),
    ("Flock Of Seagulls", "I Ran"),
    ("Kajagoogoo", "Too Shy"),
    ("Thomas Dolby", "She Blinded Me With Science"),
    ("Gary Numan", "Cars"),
    ("OMD", "If You Leave"),
    ("Alphaville", "Forever Young"),
    ("Tears For Fears", "Mad World"),
    ("Simple Minds", "Don't You Forget About Me"),
    ("The Outfield", "Your Love"),
    ("Cutting Crew", "I Just Died In Your Arms"),
    ("Naked Eyes", "Always Something There To Remind Me"),
    ("Wang Chung", "Everybody Have Fun Tonight"),
    ("Men At Work", "Down Under"),
    ("Men At Work", "Who Can It Be Now"),
    ("INXS", "Need You Tonight"),
    ("INXS", "Never Tear Us Apart"),
    ("Crowded House", "Don't Dream Its Over"),
    ("Midnight Oil", "Beds Are Burning"),
    ("Icehouse", "Electric Blue"),
    ("Spandau Ballet", "True"),
    ("Duran Duran", "Rio"),
    ("Duran Duran", "Ordinary World"),
    ("Thompson Twins", "Hold Me Now"),
    ("Bananarama", "Venus"),
    ("Erasure", "A Little Respect"),
    ("The Fixx", "One Thing Leads To Another"),
    ("Level 42", "Lessons In Love"),
    ("Howard Jones", "Things Can Only Get Better"),
    ("Nik Kershaw", "The Riddle"),
    ("Go West", "King Of Wishful Thinking"),
    ("T'Pau", "Heart And Soul"),
    ("Cock Robin", "When Your Heart Breaks Down"),
]

def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))

def search_uri(artist, track, cache):
    """Search for Spotify URI via DuckDuckGo."""
    key = f"{artist}|{track}"
    if key in cache:
        return cache[key]

    try:
        query = urllib.parse.quote(f"{artist} {track} spotify track")
        url = f"https://html.duckduckgo.com/html/?q={query}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

        pattern = r'open\.spotify\.com/track/([a-zA-Z0-9]+)'
        matches = re.findall(pattern, html)

        if matches:
            uri = f"spotify:track:{matches[0]}"
            cache[key] = uri
            return uri
    except Exception as e:
        print(f"    Search error: {e}")

    cache[key] = None
    return None

def fetch_lyrics(artist, track):
    """Fetch synced lyrics from LRCLIB."""
    try:
        query = urllib.parse.urlencode({
            "artist_name": artist,
            "track_name": track
        })
        url = f"https://lrclib.net/api/get?{query}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'claude-dj/1.0'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        synced = data.get("syncedLyrics", "")
        if not synced:
            return []

        lines = []
        for line in synced.split("\n"):
            line = line.strip()
            if not line:
                continue
            match = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)', line)
            if match:
                mins = int(match.group(1))
                secs = float(match.group(2))
                timestamp = mins * 60 + secs
                text = match.group(3).strip()
                if text:
                    lines.append({"time": timestamp, "text": text})

        return lines
    except:
        return []

def extract_words(text):
    text = re.sub(r"[^\w\s'-]", "", text.lower())
    words = text.split()
    return [w.strip("'-") for w in words if w.strip("'-")]

def main():
    print(f"Processing {len(SONGS)} songs...\n")

    cache = load_cache()
    word_index = defaultdict(list)

    success = 0
    no_uri = 0
    no_lyrics = 0

    for i, (artist, track) in enumerate(SONGS):
        print(f"[{i+1}/{len(SONGS)}] {artist} - {track}")

        # Get URI
        uri = search_uri(artist, track, cache)
        if not uri:
            print("    No URI found")
            no_uri += 1
            time.sleep(0.5)
            continue

        # Get lyrics
        lyrics = fetch_lyrics(artist, track)
        if not lyrics:
            print(f"    No lyrics ({uri})")
            no_lyrics += 1
            time.sleep(0.3)
            continue

        print(f"    {len(lyrics)} lines")
        success += 1

        # Index words
        for line in lyrics:
            words = extract_words(line["text"])
            for word in words:
                if len(word) < 2:
                    continue
                word_index[word].append({
                    "artist": artist,
                    "track": track,
                    "uri": uri,
                    "time": round(line["time"], 2),
                    "line": line["text"],
                    "duration": 1.5
                })

        time.sleep(0.3)  # Be nice to APIs

        # Save cache periodically
        if i % 20 == 0:
            save_cache(cache)

    save_cache(cache)

    # Save word index
    output = {k: v for k, v in sorted(word_index.items())}
    with open(WORDS_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Done!")
    print(f"  Successful: {success}")
    print(f"  No URI: {no_uri}")
    print(f"  No lyrics: {no_lyrics}")
    print(f"  Unique words: {len(word_index)}")
    print(f"  Total entries: {sum(len(v) for v in word_index.values())}")
    print(f"\nSaved to {WORDS_FILE}")

if __name__ == "__main__":
    main()
