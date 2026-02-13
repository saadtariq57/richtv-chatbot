"""
Context Builder - Normalizes data from fetchers into structured JSON.

Now primarily responsible for lightweight extraction (e.g., ticker)
from the raw user query so the orchestrator can call real APIs.
"""

import re
from typing import Optional


_NON_TICKER_WORDS = {
    # Common words
    "WHAT", "IS", "THE", "PRICE", "OF", "STOCK", "ON", "TODAY", "TELL", "ME",
    "ABOUT", "AND", "FOR", "A", "AN", "IN", "TO", "AT", "HOW", "MUCH", "WAS",
    "WERE", "ARE", "SHOW", "RIGHT", "NOW", "LAST", "MONTH", "YEAR", "WEEK",
    "DAY", "THIS", "THAT", "THESE", "THOSE", "WITH", "FROM", "BY", "AS",
    "IT", "ITS", "HIS", "HER", "THEIR", "OUR", "YOUR", "MY", "CAN", "WILL",
    "SHOULD", "WOULD", "COULD", "MAY", "MIGHT", "MUST", "HAVE", "HAS", "HAD",
    "DO", "DOES", "DID", "GET", "GOT", "GIVE", "GAVE", "SEE", "SAW", "KNOW",
    "KNEW", "THINK", "THOUGHT", "SAY", "SAID", "GO", "WENT", "COME", "CAME",
    "MAKE", "MADE", "TAKE", "TOOK", "USE", "USED", "FIND", "FOUND", "WORK",
    "WORKED", "CALL", "CALLED", "TRY", "TRIED", "ASK", "ASKED", "NEED",
    "NEEDED", "WANT", "WANTED", "LOOK", "LOOKED", "SEEM", "SEEMED", "FEEL",
    "FELT", "BECOME", "BECAME", "LEAVE", "LEFT", "PUT", "MEAN", "MEANT",
    "KEEP", "KEPT", "LET", "BEGIN", "BEGAN", "SHOW", "SHOWN", "HEAR", "HEARD",
    "PLAY", "PLAYED", "RUN", "RAN", "MOVE", "MOVED", "LIVE", "LIVED", "BELIEVE",
    "BELIEVED", "BRING", "BROUGHT", "HAPPEN", "HAPPENED", "WRITE", "WROTE",
    "SIT", "SAT", "STAND", "STOOD", "LOSE", "LOST", "PAY", "PAID", "MEET",
    "MET", "INCLUDE", "INCLUDED", "CONTINUE", "CONTINUED", "SET", "LEAD",
    "LED", "UNDERSTAND", "UNDERSTOOD", "WATCH", "WATCHED", "FOLLOW", "FOLLOWED",
    "STOP", "STOPPED", "CREATE", "CREATED", "SPEAK", "SPOKE", "READ", "READ",
    "ALLOW", "ALLOWED", "ADD", "ADDED", "SPEND", "SPENT", "GROW", "GREW",
    "OPEN", "OPENED", "WALK", "WALKED", "WIN", "WON", "OFFER", "OFFERED",
    "REMEMBER", "REMEMBERED", "LOVE", "LOVED", "CONSIDER", "CONSIDERED",
    "APPEAR", "APPEARED", "BUY", "BOUGHT", "WAIT", "WAITED", "SERVE", "SERVED",
    "DIE", "DIED", "SEND", "SENT", "BUILD", "BUILT", "STAY", "STAYED",
    "FALL", "FELL", "CUT", "CUT", "REACH", "REACHED", "KILL", "KILLED",
    "RAISE", "RAISED", "PASS", "PASSED", "SELL", "SOLD", "DECIDE", "DECIDED",
    "RETURN", "RETURNED", "EXPLAIN", "EXPLAINED", "DEVELOP", "DEVELOPED",
    "CARRY", "CARRIED", "BREAK", "BROKE", "RECEIVE", "RECEIVED", "AGREE",
    "AGREED", "SUPPORT", "SUPPORTED", "HIT", "HIT", "PRODUCE", "PRODUCED",
    "EAT", "ATE", "COVER", "COVERED", "CATCH", "CAUGHT", "DRAW", "DREW",
    "CHOOSE", "CHOSE", "SUCCEED", "SUCCEEDED", "SHOOT", "SHOT", "TEACH",
    "TAUGHT", "LEARN", "LEARNED", "DROP", "DROPPED", "INCREASE", "INCREASED",
    "FORGET", "FORGOT", "INTRODUCE", "INTRODUCED", "MARRY", "MARRIED",
    "ENJOY", "ENJOYED", "CONTROL", "CONTROLLED", "DESCRIBE", "DESCRIBED",
    "REMOVE", "REMOVED", "REMEMBER", "REMEMBERED", "IMPROVE", "IMPROVED",
    "PREPARE", "PREPARED", "DESTROY", "DESTROYED", "REFUSE", "REFUSED",
    "IMAGINE", "IMAGINED", "PROVIDE", "PROVIDED", "REQUIRE", "REQUIRED",
    "REPLACE", "REPLACED", "REALIZE", "REALIZED", "REPRESENT", "REPRESENTED",
    "REDUCE", "REDUCED", "REFER", "REFERRED", "RELATE", "RELATED", "REMAIN",
    "REMAINED", "REMOVE", "REMOVED", "REPEAT", "REPEATED", "REPLY", "REPLIED",
    "REPORT", "REPORTED", "REPRESENT", "REPRESENTED", "REQUEST", "REQUESTED",
    "RESEARCH", "RESEARCHED", "RESPOND", "RESPONDED", "REST", "RESTED",
    "RESULT", "RESULTED", "RETURN", "RETURNED", "REVEAL", "REVEALED",
    "REVIEW", "REVIEWED", "RIDE", "RODE", "RING", "RANG", "RISE", "ROSE",
    "RISK", "RISKED", "ROCK", "ROCKED", "ROLL", "ROLLED", "ROOM", "ROOMED",
    "ROOT", "ROOTED", "ROPE", "ROPED", "ROSE", "ROSED", "ROUGH", "ROUGHED",
    "ROUND", "ROUNDED", "ROW", "ROWED", "RUB", "RUBBED", "RULE", "RULED",
    "RUN", "RAN", "RUSH", "RUSHED", "SAFE", "SAFED", "SAID", "SAIL", "SAILED",
    "SALT", "SALTED", "SAME", "SAMED", "SAND", "SANDED", "SAVE", "SAVED",
    "SAW", "SAWED", "SAY", "SAID", "SCALE", "SCALED", "SCENE", "SCENED",
    "SCHOOL", "SCHOOLED", "SCIENCE", "SCIENCED", "SCORE", "SCORED", "SCREEN",
    "SCREENED", "SEA", "SEAED", "SEARCH", "SEARCHED", "SEASON", "SEASONED",
    "SEAT", "SEATED", "SECOND", "SECONDED", "SECRET", "SECRETED", "SECTION",
    "SECTIONED", "SEE", "SAW", "SEED", "SEEDED", "SEEK", "SOUGHT", "SEEM",
    "SEEMED", "SELL", "SOLD", "SEND", "SENT", "SENSE", "SENSED", "SENTENCE",
    "SENTENCED", "SERIES", "SERIESED", "SERIOUS", "SERIOUSED", "SERVE",
    "SERVED", "SERVICE", "SERVICED", "SET", "SET", "SETTLE", "SETTLED",
    "SEVEN", "SEVENED", "SEVERAL", "SEVERALED", "SEX", "SEXED", "SHADE",
    "SHADED", "SHADOW", "SHADOWED", "SHAKE", "SHOOK", "SHALL", "SHALLED",
    "SHAPE", "SHAPED", "SHARE", "SHARED", "SHARP", "SHARPED", "SHE", "SHED",
    "SHEET", "SHEETED", "SHELF", "SHELVED", "SHELL", "SHELLED", "SHELTER",
    "SHELTERED", "SHIFT", "SHIFTED", "SHINE", "SHONE", "SHIP", "SHIPPED",
    "SHIRT", "SHIRTED", "SHOCK", "SHOCKED", "SHOE", "SHOED", "SHOOT", "SHOT",
    "SHOP", "SHOPPED", "SHORE", "SHORED", "SHORT", "SHORTED", "SHOT", "SHOTTED",
    "SHOULD", "SHOULDED", "SHOULDER", "SHOULDERED", "SHOUT", "SHOUTED",
    "SHOW", "SHOWED", "SHUT", "SHUTTED", "SICK", "SICKED", "SIDE", "SIDED",
    "SIGHT", "SIGHTED", "SIGN", "SIGNED", "SIGNAL", "SIGNALED", "SILENCE",
    "SILENCED", "SILENT", "SILENTED", "SILK", "SILKED", "SILLY", "SILLIED",
    "SILVER", "SILVERED", "SIMILAR", "SIMILARED", "SIMPLE", "SIMPLED",
    "SIMPLY", "SIMPLIED", "SINCE", "SINCED", "SING", "SANG", "SINGLE",
    "SINGLED", "SINK", "SANK", "SIR", "SIRED", "SISTER", "SISTERED", "SIT",
    "SAT", "SITE", "SITED", "SITUATION", "SITUATED", "SIX", "SIXED", "SIZE",
    "SIZED", "SKILL", "SKILLED", "SKIN", "SKINNED", "SKY", "SKIED", "SLAVE",
    "SLAVED", "SLEEP", "SLEPT", "SLIDE", "SLID", "SLIGHT", "SLIGHTED",
    "SLIP", "SLIPPED", "SLOW", "SLOWED", "SMALL", "SMALLED", "SMART", "SMARTED",
    "SMELL", "SMELT", "SMILE", "SMILED", "SMOKE", "SMOKED", "SMOOTH", "SMOOTHED",
    "SNAKE", "SNAKED", "SNOW", "SNOWED", "SO", "SOED", "SOAP", "SOAPED",
    "SOCIAL", "SOCIALED", "SOCIETY", "SOCIETIED", "SOCK", "SOCKED", "SOFT",
    "SOFTED", "SOIL", "SOILED", "SOLDIER", "SOLDIERED", "SOLID", "SOLIDED",
    "SOLUTION", "SOLUTIONED", "SOLVE", "SOLVED", "SOME", "SOMED", "SON",
    "SONNED", "SONG", "SONGED", "SOON", "SOONED", "SORRY", "SORRIED",
    "SORT", "SORTED", "SOUL", "SOULED", "SOUND", "SOUNDED", "SOUP", "SOUPED",
    "SOUTH", "SOUTHED", "SPACE", "SPACED", "SPEAK", "SPOKE", "SPECIAL",
    "SPECIALED", "SPEECH", "SPEECHED", "SPEED", "SPED", "SPELL", "SPELT",
    "SPEND", "SPENT", "SPIRIT", "SPIRITED", "SPLIT", "SPLITTED", "SPOKE",
    "SPOKEN", "SPORT", "SPORTED", "SPOT", "SPOTTED", "SPREAD", "SPREAD",
    "SPRING", "SPRANG", "SQUARE", "SQUARED", "STAGE", "STAGED", "STAIR",
    "STAIRED", "STAKE", "STAKED", "STAND", "STOOD", "STANDARD", "STANDARDED",
    "STAR", "STARRED", "STARE", "STARED", "START", "STARTED", "STATE",
    "STATED", "STATION", "STATIONED", "STAY", "STAYED", "STEAL", "STOLE",
    "STEAM", "STEAMED", "STEEL", "STEELED", "STEP", "STEPPED", "STICK",
    "STUCK", "STILL", "STILLED", "STOCK", "STOCKED", "STOMACH", "STOMACHED",
    "STONE", "STONED", "STOP", "STOPPED", "STORE", "STORED", "STORM",
    "STORMED", "STORY", "STORIED", "STRAIGHT", "STRAIGHTED", "STRANGE",
    "STRANGED", "STREAM", "STREAMED", "STREET", "STREETED", "STRENGTH",
    "STRENGTHED", "STRESS", "STRESSED", "STRETCH", "STRETCHED", "STRIKE",
    "STRUCK", "STRING", "STRUNG", "STRIP", "STRIPPED", "STRONG", "STRONGED",
    "STRUCTURE", "STRUCTURED", "STRUGGLE", "STRUGGLED", "STUDENT", "STUDENTED",
    "STUDY", "STUDIED", "STUFF", "STUFFED", "STYLE", "STYLED", "SUBJECT",
    "SUBJECTED", "SUBSTANCE", "SUBSTANCED", "SUCCESS", "SUCCESSED",
    "SUCCESSFUL", "SUCCESSFULLED", "SUCH", "SUCHED", "SUDDEN", "SUDDENED",
    "SUFFER", "SUFFERED", "SUGAR", "SUGARED", "SUGGEST", "SUGGESTED",
    "SUIT", "SUITED", "SUMMER", "SUMMERED", "SUN", "SUNNED", "SUPPLY",
    "SUPPLIED", "SUPPORT", "SUPPORTED", "SUPPOSE", "SUPPOSED", "SURE",
    "SURED", "SURFACE", "SURFACED", "SURPRISE", "SURPRISED", "SURROUND",
    "SURROUNDED", "SUSPECT", "SUSPECTED", "SUSPEND", "SUSPENDED", "SWALLOW",
    "SWALLOWED", "SWEET", "SWEETED", "SWIM", "SWAM", "SWING", "SWUNG",
    "SWITCH", "SWITCHED", "SYMBOL", "SYMBOLED", "SYSTEM", "SYSTEMED",
    "TABLE", "TABLED", "TAIL", "TAILED", "TAKE", "TOOK", "TALE", "TALED",
    "TALK", "TALKED", "TALL", "TALLED", "TANK", "TANKED", "TAPE", "TAPED",
    "TARGET", "TARGETED", "TASK", "TASKED", "TASTE", "TASTED", "TAX", "TAXED",
    "TEA", "TEAED", "TEACH", "TAUGHT", "TEAM", "TEAMED", "TEAR", "TORE",
    "TECHNICAL", "TECHNICALED", "TECHNIQUE", "TECHNIQUED", "TELEPHONE",
    "TELEPHONED", "TELEVISION", "TELEVISIONED", "TELL", "TOLD", "TEMPERATURE",
    "TEMPERATURED", "TEN", "TENNED", "TEND", "TENDED", "TERM", "TERMED",
    "TERRIBLE", "TERRIBLED", "TEST", "TESTED", "THAN", "THANED", "THANK",
    "THANKED", "THAT", "THATED", "THE", "THEED", "THEATRE", "THEATRED",
    "THEIR", "THEIRED", "THEM", "THEMED", "THEME", "THEMED", "THEN",
    "THENED", "THEORY", "THEORIED", "THERE", "THERED", "THEREFORE", "THEREFORED",
    "THESE", "THESED", "THEY", "THEYED", "THICK", "THICKED", "THIN", "THINNED",
    "THING", "THINGED", "THINK", "THOUGHT", "THIRD", "THIRDED", "THIS",
    "THISED", "THOSE", "THOSED", "THOUGH", "THOUGHED", "THOUGHT", "THOUGHTED",
    "THOUSAND", "THOUSANDED", "THREAT", "THREATED", "THREE", "THREED",
    "THROUGH", "THROUGHED", "THROW", "THREW", "THUMB", "THUMBED", "THUS",
    "THUSED", "TICKET", "TICKETED", "TIE", "TIED", "TIGHT", "TIGHTED",
    "TILL", "TILLED", "TIME", "TIMED", "TIN", "TINNED", "TINY", "TINIED",
    "TIP", "TIPPED", "TIRE", "TIRED", "TITLE", "TITLED", "TO", "TOED",
    "TOAST", "TOASTED", "TOBACCO", "TOBACCOED", "TODAY", "TODAYED", "TOE",
    "TOED", "TOGETHER", "TOGETHERED", "TOMORROW", "TOMORROWED", "TONE",
    "TONED", "TONGUE", "TONGUED", "TONIGHT", "TONIGHTED", "TOO", "TOOED",
    "TOOL", "TOOLED", "TOOTH", "TOOTHED", "TOP", "TOPPED", "TOPIC", "TOPICED",
    "TOTAL", "TOTALED", "TOUCH", "TOUCHED", "TOUGH", "TOUGHED", "TOUR",
    "TOURED", "TOWARD", "TOWARDED", "TOWER", "TOWERED", "TOWN", "TOWNED",
    "TRACK", "TRACKED", "TRADE", "TRADED", "TRADITION", "TRADITIONED",
    "TRAFFIC", "TRAFFICED", "TRAIN", "TRAINED", "TRANSFER", "TRANSFERRED",
    "TRANSFORM", "TRANSFORMED", "TRANSPORT", "TRANSPORTED", "TRAP", "TRAPPED",
    "TRAVEL", "TRAVELED", "TREAT", "TREATED", "TREATMENT", "TREATMENTED",
    "TREE", "TREED", "TREND", "TRENDED", "TRIAL", "TRIALED", "TRIBE",
    "TRIBED", "TRICK", "TRICKED", "TRIP", "TRIPPED", "TROOP", "TROOPED",
    "TROUBLE", "TROUBLED", "TRUCK", "TRUCKED", "TRUE", "TRUED", "TRULY",
    "TRULIED", "TRUST", "TRUSTED", "TRUTH", "TRUTHED", "TRY", "TRIED",
    "TUBE", "TUBED", "TUNE", "TUNED", "TURN", "TURNED", "TWELVE", "TWELVED",
    "TWENTY", "TWENTIED", "TWICE", "TWICED", "TWIN", "TWINNED", "TWO",
    "TWOED", "TYPE", "TYPED", "TYPICAL", "TYPICALED", "UGLY", "UGLIED",
    "ULTIMATE", "ULTIMATED", "UNABLE", "UNABLED", "UNCLE", "UNCLED",
    "UNDER", "UNDERED", "UNDERSTAND", "UNDERSTOOD", "UNDERSTANDING",
    "UNDERSTANDINGED", "UNION", "UNIONED", "UNIT", "UNITED", "UNITED",
    "UNITEDED", "UNIVERSAL", "UNIVERSALED", "UNIVERSE", "UNIVERSED",
    "UNIVERSITY", "UNIVERSITIED", "UNKNOWN", "UNKNOWNED", "UNLESS", "UNLESSED",
    "UNLIKE", "UNLIKED", "UNTIL", "UNTILED", "UNUSUAL", "UNUSUALED", "UP",
    "UPPED", "UPON", "UPONED", "UPPER", "UPPERED", "URBAN", "URBANED",
    "URGE", "URGED", "US", "USED", "USE", "USED", "USED", "USEFUL",
    "USEFULED", "USER", "USERED", "USUAL", "USUALED", "USUALLY", "USUALLIED",
    "VALUE", "VALUED", "VARIABLE", "VARIABLED", "VARIETY", "VARIETIED",
    "VARIOUS", "VARIOUSED", "VAST", "VASTED", "VEGETABLE", "VEGETABLED",
    "VEHICLE", "VEHICLED", "VERSION", "VERSIONED", "VERY", "VERIED",
    "VIA", "VIAED", "VICTIM", "VICTIMED", "VICTORY", "VICTORIED", "VIDEO",
    "VIDEOED", "VIEW", "VIEWED", "VILLAGE", "VILLAGED", "VIOLENCE", "VIOLENCED",
    "VIOLENT", "VIOLENTED", "VIRTUAL", "VIRTUALED", "VIRTUE", "VIRTUED",
    "VIRUS", "VIRUSED", "VISIBLE", "VISIBLED", "VISION", "VISIONED", "VISIT",
    "VISITED", "VISITOR", "VISITORED", "VISUAL", "VISUALED", "VITAL",
    "VITALED", "VOICE", "VOICED", "VOLUME", "VOLUMED", "VOLUNTARY", "VOLUNTARIED",
    "VOTE", "VOTED", "WAGE", "WAGED", "WAIT", "WAITED", "WAKE", "WOKE",
    "WALK", "WALKED", "WALL", "WALLED", "WANT", "WANTED", "WAR", "WARRED",
    "WARM", "WARMED", "WARN", "WARNED", "WASH", "WASHED", "WASTE", "WASTED",
    "WATCH", "WATCHED", "WATER", "WATERED", "WAVE", "WAVED", "WAY", "WAYED",
    "WE", "WEED", "WEAK", "WEAKED", "WEALTH", "WEALTHED", "WEAPON", "WEAPONED",
    "WEAR", "WORE", "WEATHER", "WEATHERED", "WEEK", "WEEKED", "WEEKEND",
    "WEEKENDED", "WEIGHT", "WEIGHTED", "WELCOME", "WELCOMED", "WELFARE",
    "WELFARED", "WELL", "WELLED", "WEST", "WESTED", "WESTERN", "WESTERNED",
    "WET", "WETTED", "WHAT", "WHATED", "WHATEVER", "WHATEVERED", "WHEEL",
    "WHEELED", "WHEN", "WHENED", "WHENEVER", "WHENEVERED", "WHERE",
    "WHEREED", "WHEREAS", "WHEREASED", "WHEREVER", "WHEREVERED", "WHETHER",
    "WHETHERED", "WHICH", "WHICHED", "WHILE", "WHILED", "WHILST", "WHILSTED",
    "WHIP", "WHIPPED", "WHISPER", "WHISPERED", "WHISTLE", "WHISTLED",
    "WHITE", "WHITED", "WHO", "WHOED", "WHOLE", "WHOLED", "WHOM", "WHOMED",
    "WHOSE", "WHOSED", "WHY", "WHYED", "WIDE", "WIDED", "WIFE", "WIFED",
    "WILD", "WILDED", "WILL", "WILLED", "WIN", "WON", "WIND", "WOUND",
    "WINDOW", "WINDOWED", "WINE", "WINED", "WING", "WINGED", "WINNER",
    "WINNERED", "WINTER", "WINTERED", "WIRE", "WIRED", "WISE", "WISED",
    "WISH", "WISHED", "WITH", "WITHED", "WITHIN", "WITHINED", "WITHOUT",
    "WITHOUTED", "WOMAN", "WOMANED", "WONDER", "WONDERED", "WONDERFUL",
    "WONDERFULLED", "WOOD", "WOODED", "WOODEN", "WOODENED", "WOOL", "WOOLLED",
    "WORD", "WORDED", "WORK", "WORKED", "WORKER", "WORKERED", "WORKING",
    "WORKINGED", "WORLD", "WORLDED", "WORRY", "WORRIED", "WORTH", "WORTHED",
    "WOULD", "WOULDED", "WRITE", "WROTE", "WRITER", "WRITERED", "WRITING",
    "WRITINGED", "WRONG", "WRONGED", "YARD", "YARDED", "YEAH", "YEAHED",
    "YEAR", "YEARED", "YELLOW", "YELLOWED", "YES", "YESED", "YESTERDAY",
    "YESTERDAYED", "YET", "YETED", "YOU", "YOUED", "YOUNG", "YOUNGED",
    "YOUR", "YOURE", "YOURS", "YOURSED", "YOURSELF", "YOURSELFED", "YOUTH",
    "YOUTHED", "ZONE", "ZONED",
}

# Common company names to ticker symbols mapping
# Covers top US companies for better UX
_COMPANY_TO_TICKER = {
    # Tech Giants
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "netflix": "NFLX",
    
    # Other Major Companies
    "disney": "DIS",
    "boeing": "BA",
    "walmart": "WMT",
    "jpmorgan": "JPM",
    "visa": "V",
    "mastercard": "MA",
    "coca-cola": "KO",
    "coke": "KO",
    "pepsi": "PEP",
    "mcdonald": "MCD",
    "mcdonalds": "MCD",
    "starbucks": "SBUX",
    "nike": "NKE",
    "ford": "F",
    "gm": "GM",
    "general motors": "GM",
    "intel": "INTC",
    "amd": "AMD",
    "qualcomm": "QCOM",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "adobe": "ADBE",
    
    # Indices (common names)
    "s&p": "^GSPC",
    "s&p 500": "^GSPC",
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dow": "^DJI",
    "dow jones": "^DJI",
}


def _extract_ticker(user_query: str) -> Optional[str]:
    """
    Heuristic ticker extraction from user query.

    Prioritizes 2-5 letter tokens (typical ticker length) and filters
    out common words. Also checks against a hardcoded mapping for
    common company names.
    """
    text = user_query.upper()
    text_lower = user_query.lower()
    
    # First, check if query contains a known company name
    for company_name, ticker in _COMPANY_TO_TICKER.items():
        # Use word boundary to avoid partial matches (e.g. "meta" in "metadata")
        if re.search(r'\b' + re.escape(company_name) + r'\b', text_lower):
            return ticker
    
    # First, check for crypto-style tickers with hyphens (e.g., BTC-USD, ETH-USD)
    crypto_candidates = re.findall(r"\b[A-Z]{2,5}-[A-Z]{2,5}\b", text)
    if crypto_candidates:
        return crypto_candidates[0]
    
    # Then, look for 2-5 letter tokens (typical ticker length)
    candidates_2_5 = re.findall(r"\b[A-Z]{2,5}\b", text)
    for token in candidates_2_5:
        if token not in _NON_TICKER_WORDS:
            return token
    
    # Fallback: single letter tokens (rare but possible)
    candidates_1 = re.findall(r"\b[A-Z]{1}\b", text)
    for token in candidates_1:
        if token not in _NON_TICKER_WORDS:
            return token
    
    return None


def is_valid_ticker(ticker: Optional[str]) -> bool:
    """
    Check if extracted ticker looks valid.
    
    Used to determine if LLM assistance is needed.
    
    Args:
        ticker: Extracted ticker string
        
    Returns:
        True if ticker looks valid, False otherwise
    """
    if not ticker or ticker == "UNKNOWN":
        return False
    
    # Real tickers are typically 1-5 characters
    if len(ticker) > 5:
        return False
    
    ticker_lower = ticker.lower()
    
    # Check if it's a known company name that wasn't resolved
    # (This would indicate ticker extraction failed)
    if ticker_lower in _COMPANY_TO_TICKER:
        # It's a company name, not a ticker symbol
        return False
    
    # Extended list of company names that might slip through
    invalid_names = {
        "apple", "microsoft", "tesla", "amazon", "google",
        "nvidia", "meta", "facebook", "netflix", "figma",
        "adobe", "oracle", "intel", "cisco", "uber",
        "lyft", "snap", "twitter", "zoom", "slack"
    }
    if ticker_lower in invalid_names:
        return False
    
    # Heuristic: if ticker is 4-5 chars and looks like a pronounceable word
    # (has vowels in word-like patterns), it's likely a company name, not a ticker
    # Real tickers are usually acronyms (e.g., AAPL, MSFT, NVDA)
    if len(ticker) >= 4:
        # Count consecutive vowels - company names tend to have them
        vowel_pattern = re.search(r'[aeiou]{2,}', ticker_lower)
        if vowel_pattern:
            # Has consecutive vowels (e.g., "figma" has "i"), likely a word
            return False
        
        # Check if it's all lowercase or mixed case (would indicate it wasn't properly extracted)
        if ticker != ticker.upper():
            return False
    
    return True


def build_context(user_query: str) -> dict:
    """
    Build initial context from user query.

    Responsibilities:
    - Extract ticker symbol (if any)
    - Capture the raw user query
    - Leave financial fields (price, fundamentals, etc.) to be
      populated by fetchers via the orchestrator.
    """
    ticker = _extract_ticker(user_query) or "UNKNOWN"

    context = {
        "ticker": ticker,
        "user_query": user_query,
        "source": "orchestrator",
    }

    return context


def normalize_context(fetcher_data: dict) -> dict:
    """
    Normalize data from multiple fetchers into unified structure.
    
    Future implementation will combine:
    - Price data from PriceFetcher
    - Fundamentals from FundamentalsFetcher
    - News from NewsFetcher
    
    Args:
        fetcher_data: Raw data from fetchers
        
    Returns:
        Normalized context dictionary
    """
    # Placeholder for future implementation
    return fetcher_data

