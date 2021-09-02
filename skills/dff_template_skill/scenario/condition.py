import logging
import re

from dff.core import Context, Actor
# import Levenshtein

#
# def small_levenshtein(desired_item: str):
#     flag = False
#     desired_item = [str(x).replace(' ', '') for x in desired_item]
#     user_uttr = [str(x).replace(' ', '') for x in ctx.last_request]
#     lev_dist = Levenshtein.distance(desired_item, user_uttr)
#     if lev_dist < 4:
#         flag = True
#
#     return flag


logger = logging.getLogger(__name__)
# ....


def has_album(album_name: str):
    def has_album_condition(ctx: Context, actor: Actor, *args, **kwargs):
        # match = re.findall(album_name, ctx.last_request, re.IGNORECASE)
        # if match:
        #     small_levenshtein()
        return bool(re.findall(album_name, ctx.last_request, re.IGNORECASE))

    return has_album_condition


def wants_to_see(item_name: str):
    def has_cond(ctx: Context, actor: Actor, *args, **kwargs):
        flag = False
        match = re.search(r"((.*i\swant\sto\ssee\s)|(.*i\swanna\ssee\s)|(.*\slook\sat\s)|"
                          r"(.*show\sme\s)|(.*tell\sme\sabout\s))(?P<item>.*)", ctx.last_request, re.I)
        item = match.group('item')
        if re.findall(item_name, item, re.I):
            flag = True
        return flag

    return has_cond



def not_visited_album(ctx: Context, actor: Actor, *args, **kwargs):
    return ctx.misc.get("album_counter", 0) < 12


def move_on(ctx: Context, actor: Actor, *args, **kwargs):
    return bool(re.findall("move on", ctx.last_request, re.IGNORECASE))


def has_songs(ctx: Context, actor: Actor, *args, **kwargs):
    songs = [
        "Hey Jude",
        "Don't Let Me Down",
        "We Can Work it Out",
        "Come Together",
        "Yellow Submarine",
        "Revolution",
        "Imagine",
        "Something",
        "Hello, Goodbye",
        "A Day In The Life",
        "Help!",
        "Penny Lane",
    ]

    songs_re = "|".join(songs)
    return bool(re.findall(songs_re, ctx.last_request, re.IGNORECASE))


def has_member(member_name: str):
    def has_membar_condition(ctx: Context, actor: Actor, *args, **kwargs):
        return bool(re.findall(member_name, ctx.last_request, re.IGNORECASE))

    return has_membar_condition


def has_correct_answer(ctx: Context, actor: Actor, *args, **kwargs):
    a = ["Abbey Road", "A Hard Day's Night"]
    ar = "|".join(a)
    return bool(re.findall(ar, ctx.last_request, re.IGNORECASE))


def has_any_album(ctx: Context, actor: Actor, *args, **kwargs):
    albums = [
        "Please Please Me",
        "With the Beatles",
        "Introducing... The Beatles",
        "Meet the Beatles!",
        "Twist and Shout",
        "The Beatles' Second Album",
        "The Beatles' Long Tall Sally",
        "A Hard Day's Night",
        "Something New",
        "Help!",
        "Sgt. Pepper's Lonely Hearts Club Band",
        "White Album",
        "The Beatles Beat",
        "Another Beatles Christmas Record",
        "Beatles '65",
        "Beatles VI",
        "Five Nights In A Judo Arena",
        "The Beatles at the Hollywood Bowl",
        "Live! at the Star-Club in Hamburg, German; 1962",
        "The Black Album",
        "20 Exitos De Oro",
        "A Doll's House",
        "The Complete Silver Beatles",
        "Rock 'n' Roll Music Vol. 1",
        "Yellow Submarine",
        "Let It Be",
        "Beatles for Sale",
        "Revolver",
        "Abbey Road",
        "Rubber Soul",
    ]

    albums_re = "|".join(albums)
    return bool(re.findall(albums_re, ctx.last_request, re.IGNORECASE))


def is_beatles_song(ctx: Context, actor: Actor, *args, **kwargs):
    songs = [
	'Title', '12-Bar Original', 'A Day in the Life', "A Hard Day's Night", 
	'A Shot of Rhythm and Blues', 'A Taste of Honey', 'Across the Universe', 'Act Naturally', 
	"Ain't She Sweet", "All I've Got to Do", 'All My Loving', 'All Things Must Pass', 'All Together Now', 
	'All You Need Is Love', 'And I Love Her', 'And Your Bird Can Sing', 'Anna (Go to Him)', 'Another Girl', 
	'Any Time at All', 'Ask Me Why', "Baby It's You", "Baby's in Black", '"Baby', 'Back in the U.S.S.R.', 
	'Bad Boy', 'Bad to Me', 'Beautiful Dreamer', 'Because I Know You Love Me So', 'Because', 'Being for the Benefit of Mr. Kite!', 
	'Birthday', 'Blackbird', 'Blue Jay Way', 'Boys', 'Bésame Mucho', "Can't Buy Me Love", 'Carol', 'Carry That Weight', 'Catswalk',
	'Cayenne', 'Chains', 'Child of Nature', 'Christmas Time (Is Here Again)', 'Circles', 'Clarabella', 'Come and Get It', 'Come Together', 
	'Cry Baby Cry', 'Cry for a Shadow', '"Crying', 'Day Tripper', 'Dear Prudence', 'Devil in Her Heart', 'Dig a Pony', 'Dig It', '"Dizzy',
	'Do You Want to Know a Secret?', 'Doctor Robert', "Don't Bother Me", "Don't Ever Change", "Don't Let Me Down", "Don't Pass Me By", 
	'Drive My Car', 'Eight Days a Week', 'Eleanor Rigby', 'Etcetera', 'Every Little Thing', 
	"Everybody's Got Something to Hide Except Me and My Monkey", "Everybody's Trying to Be My Baby", 'Fancy My Chances with You', 
	'Fixing a Hole', 'Flying', 'For No One', 'For You Blue', 'Free as a Bird', 'From Me to You', 'From Us to You', 'Get Back', 
	'Getting Better', 'Girl', 'Glad All Over', 'Glass Onion', 'Golden Slumbers', 'Good Day Sunshine', '"Good Morning', 'Good Night', 
	'Goodbye', 'Got to Get You into My Life', '"Hallelujah', 'Happiness Is a Warm Gun', 'Heather', 'Hello Little Girl', '"Hello', 
	'Help!', 'Helter Skelter', 'Her Majesty', 'Here Comes the Sun', '"Here', 'Hey Bulldog', 'Hey Jude', 'Hippy Hippy Shake', 
	'Hold Me Tight', "Honey Don't", 'Honey Pie', 'How Do You Do It?', 'I Am the Walrus', 'I Call Your Name', "I Don't Want to Spoil the Party", 
	'I Feel Fine', 'I Forgot to Remember to Forget', 'I Got a Woman', 'I Got to Find My Baby', "I Just Don't Understand", 'I Lost My Little Girl', 
	'I Me Mine', 'I Need You', 'I Saw Her Standing There', 'I Should Have Known Better', 'I Wanna Be Your Man', 'I Want to Hold Your Hand', 
	'I Want to Tell You', "I Want You (She's So Heavy)", 'I Will', "I'll Be Back", "I'll Be on My Way", "I'll Cry Instead", "I'll Follow the Sun", 
	"I'll Get You", "I'll Keep You Satisfied", "I'm a Loser", "I'm Down", "I'm Gonna Sit Right Down and Cry (Over You)", 
	"I'm Happy Just to Dance with You", "I'm In Love", "I'm Looking Through You", "I'm Only Sleeping", "I'm So Tired", "I'm Talking About You", 
	"I'm Talking About You", "I've Got a Feeling", "I've Just Seen a Face", 'If I Fell', 'If I Needed Someone', "If You've Got Trouble", 
	'In My Life', 'In Spite of All the Danger', "It Won't Be Long", "It's All Too Much", "It's Only Love", 'Jazz Piano Song', "Jessie's Dream", 
	'Johnny B. Goode', 'Julia', 'Junk', '"Kansas City/Hey', 'Keep Your Hands Off My Baby', 'Komm Gib Mir Deine Hand', 'Lady Madonna', 
	'Leave My Kitten Alone', 'Lend Me Your Comb', 'Let It Be', 'Like Dreamers Do', 'Little Child', 'Lonesome Tears in My Eyes', 'Long Tall Sally', 
	'"Long', 'Looking Glass', 'Love Me Do', 'Love of the Loved', 'Love You To', 'Lovely Rita', 'Lucille', 'Lucy in the Sky with Diamonds', 'Madman', 
	'Maggie Mae', 'Magical Mystery Tour', '"Mailman', 'Martha My Dear', 'Matchbox', "Maxwell's Silver Hammer", 'Mean Mr. Mustard', '"Memphis', 
	'Michelle', 'Misery', "Money (That's What I Want)", 'Moonlight Bay', "Mother Nature's Son", 'Mr. Moonlight', 'My Bonnie', 'No Reply', 
	'Norwegian Wood (This Bird Has Flown)', 'Not a Second Time', 'Not Guilty', "Nothin' Shakin' (But the Leaves on the Trees)", 'Nowhere Man', 
	'"Ob-La-Di', "Octopus's Garden", 'Oh! Darling', 'Old Brown Shoe', 'One After 909', 'One and One Is Two', 'Only a Northern Song', 'Ooh! My Soul', 
	'P.S. I Love You', 'Paperback Writer', 'Penny Lane', 'Piggies', 'Please Mr. Postman', 'Please Please Me', 'Polythene Pam', 'Rain', 'Real Love', 
	'Revolution 1', 'Revolution 9', 'Revolution', '"Rip It Up/Shake', 'Rock and Roll Music', 'Rocky Raccoon', 'Roll Over Beethoven', 
	'Run for Your Life', 'Savoy Truffle', "Searchin'", 'September in the Rain', 'Sexy Sadie', "Sgt. Pepper's Lonely Hearts Club Band (Reprise)", 
	"Sgt. Pepper's Lonely Hearts Club Band", "Shakin' in the Sixties", 'She Came in Through the Bathroom Window', 'She Loves You', 
	'She Said She Said', "She's a Woman", "She's Leaving Home", 'Shout', 'Sie Liebt Dich', 'Slow Down', 'So How Come (No One Loves Me)', 
	'Soldier of Love (Lay Down Your Arms)', 'Some Other Guy', 'Something', 'Sour Milk Sea', 'Step Inside Love/Los Paranoias', 
	'Strawberry Fields Forever', 'Sun King', 'Sure to Fall (In Love with You)', 'Sweet Little Sixteen', 'Take Good Care of My Baby', 
	'Taking a Trip to Carolina', 'Taxman', 'Teddy Boy', 'Tell Me What You See', 'Tell Me Why', 'Thank You Girl', 'That Means a Lot', 
	"That'll Be the Day", "That's All Right (Mama)", 'The Ballad of John and Yoko', 'The Continuing Story of Bungalow Bill', 'The End', 
	'The Fool on the Hill', 'The Honeymoon Song', 'The Inner Light', 'The Long and Winding Road', 'The Night Before', 'The Saints', 
	'The Sheik of Araby', 'The Word', "There's a Place", 'Things We Said Today', 'Think for Yourself', 'This Boy', 'Three Cool Cats', 
	'Ticket to Ride', 'Till There Was You', 'Tip of My Tongue', 'To Know Her is to Love Her', 'Tomorrow Never Knows', 'Too Much Monkey Business', 
	'Twist and Shout', 'Two of Us', 'Wait', 'Watching Rainbows', 'We Can Work It Out', 'What Goes On', "What You're Doing", 
	"What's The New Mary Jane", 'When I Get Home', "When I'm Sixty-Four", 'While My Guitar Gently Weeps', "Why Don't We Do It in the Road?", 
	'Wild Honey Pie', "Winston's Walk", 'With a Little Help from My Friends', 'Within You Without You', 'Woman', 'Words of Love', 
	'Yellow Submarine', 'Yer Blues', 'Yes It Is', 'Yesterday', "You Can't Do That", 'You Know My Name (Look Up the Number)', 
	'You Know What to Do', 'You Like Me Too Much', 'You Never Give Me Your Money', "You Won't See Me", "You'll Be Mine", 
	"You're Going to Lose That Girl", "You've Got to Hide Your Love Away", "You've Really Got a Hold on Me", 'Young Blood', 
        'Your Mother Should Know'
    ]
    songs_re = "|".join(songs)
    return bool(re.findall(songs_re, ctx.last_request, re.IGNORECASE))




