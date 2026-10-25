# Topic bank review (decision D05)

**For:** the researcher, before approving D05. **Status:** every question and
every review decision here is a proposal written by an AI agent. Nothing is
approved. **Date:** 2026-10-19.

Part of the Batch 1 review package; start at
[`RESEARCHER_REVIEW.md`](RESEARCHER_REVIEW.md).

---

## 1. What the topic bank is, and why it must be new

Every prompt in the pilot asks a model an everyday question and attaches at
most one formatting instruction, for example:

> Why do your fingers turn pale and stiff in icy weather?
>
> Answer in 60 to 120 words.
>
> 1. Use the word indeed exactly 4 times.

The question is the **topic**. It gives the model something ordinary to write
about, so that what we measure is whether the model follows the instruction,
not whether it knows the subject. The bank holds **576 questions, 48 in each
of 12 categories**. A fixed random rule (by topic id) splits it:

| part | questions | used for |
|---|---|---|
| Stage 1 | 32 | the first pilot round: every instruction is tried on these |
| Stage 2 | 64 | the second pilot round, only for instructions whose first-round result was borderline |
| reserved confirmatory set | 480 | kept unseen for the later experiment (Batch 2); no Batch 1 code reads it |

**Why the questions must be independent of earlier studies.** Earlier DCI
studies used about 1,500 questions of their own. The models were not
trained on our earlier runs, so the concern is not memory. It is that:

- **the pilot is meant to be a fresh measurement.** Reusing a historical
  question in different words partly repeats an old measurement and weakens
  the claim that the calibration is independent;
- **the reserved set must be unseen.** The confirmatory experiment's
  evidence should not rest on questions whose answers the research team has
  already looked at in earlier work.

**What was wrong with the original 11.** The previous check compared
questions by shared words. The re-audit found 11 questions that ask the same
thing as a historical question in different words, which a word-overlap
test cannot see. For example:

| new question | historical question |
|---|---|
| Why is lightning seen before the thunder is heard? | Why does thunder arrive noticeably later than the lightning flash that caused it? |
| How does a magnifying glass make small things look larger? | Explain how a magnifying glass enlarges an image. |

Five of the 11 were pilot questions (4 in Stage 1, 1 in Stage 2) and six
were reserved. One had been introduced by the previous round of rewrites.

## 2. What was done

1. **The 11 named restatements were rewritten.** Each keeps its topic id and
   category, so its pilot or confirmatory assignment does not move.
2. **A semantic review of the whole bank found 49 more.** Because a check
   that misses 11 restatements probably misses others, every one of the 576
   questions was read against all 1,472 distinct historical questions by
   four independent AI reviewers (method in §4). They found 60
   restatements in total. All 11 the re-audit named were among them, which is
   evidence the review is sensitive. They also found 6 pairs of near-duplicate
   questions inside the new bank, and 87 questions on the same narrow subject
   as a historical one but asking something different ("close").
3. **88 questions were rewritten:**

   | reason | questions |
   |---|---|
   | restatement named by the re-audit | 11 |
   | restatement found by the semantic review | 49 |
   | one question of each internal duplicate pair (the sixth pair's two questions were both restatements) | 5 |
   | "close" cases judged to share most of their answer with a historical question | 23 |
   | **total** | **88** |

   By where they are used: **7 Stage 1, 10 Stage 2, 71 reserved.** By
   category: everyday science 17, food 14, geography 11, health and the body
   9, history 8, art and design 6, the natural world 5, work and
   organisations 5, music 4, language and writing 3, sport 3, technology 3.
4. **The replacements were checked twice more** (§4), and the screens were
   strengthened (a rare-word rule; a binding to the semantic review record).

The other 63 "close" questions were kept, plus 4 replacements that the later
passes judged close (67 in all): they share a subject but ask a different
question (for example, "Why do old tennis balls bounce differently
from new ones?" against "Why do tennis players bounce the ball several
times before serving?"). Each is listed with its rationale in
[`topic_screen_report.md`](topic_screen_report.md).

## 3. The replacements

**Read these before approving D05.** "Used in" is the part of the bank the
topic id belongs to; it did not change.

<!-- BEGIN GENERATED: topic replacement tables (python -m dci.batch1 write-review-artifacts) -->

### 3a. The 11 restatements named by the re-audit

| topic id | category | used in | original question | replacement | question it overlapped *(source)* | reason |
|---|---|---|---|---|---|---|
| `b1-everyday-science-03` | everyday science | Stage 1 (pilot) | Why do your ears pop when driving up a steep hill? | **Why do your fingers turn pale and stiff in icy weather?** | Why do your ears pop when a plane climbs or a car descends a mountain? *(dci1/v2,dci1v3)* | restatement (named by the re-audit) |
| `b1-everyday-science-04` | everyday science | Stage 1 (pilot) | How does a magnifying glass make small things look larger? | **How does a periscope let someone see over a high wall?** | Explain how a magnifying glass enlarges an image. *(dci/v19/task_bank)* | restatement (named by the re-audit) |
| `b1-history-28` | history | Stage 1 (pilot) | How did the first universities come into being? | **How did shorthand writing become a valued business skill?** *(changed again on 2026-10-25, §3c)* | How did the first universities emerge in medieval towns, and whom did they serve? *(dci1/v2,dci1v3)* | restatement (named by the re-audit) |
| `b1-technology-20` | technology | Stage 1 (pilot) | How does voice recognition cope with different accents? | **How does a smartwatch estimate the steps someone takes?** *(changed again on 2026-10-25, §3c)* | What makes voice assistants struggle with accents and background noise? *(dci1/v2,dci1v3)* | restatement (named by the re-audit) |
| `b1-food-42` | food | Stage 2 (pilot) | How does a sourdough starter keep going for years? | **How does vanilla develop its flavour inside a cured pod?** | Explain how a sourdough starter stays alive between bakes. *(dci/v19/task_bank)* | restatement (named by the re-audit) |
| `b1-everyday-science-02` | everyday science | reserved confirmatory | Why does a kernel of popcorn burst open when heated? | **Why does a block of ice stick to a dry finger?** | Why does popcorn burst open while other dried grains simply scorch? *(dci1/v2,dci1v3)* | restatement (named by the re-audit) |
| `b1-everyday-science-40` | everyday science | reserved confirmatory | Why do some fabrics crackle with static when pulled off in winter? | **Why do air bubbles in a jar of honey rise so slowly?** | Why do some fabrics build up a shock when you pull them apart? *(dci1v4)* | restatement (named by the re-audit) |
| `b1-everyday-science-41` | everyday science | reserved confirmatory | Why is lightning seen before the thunder is heard? | **Why do bicycle brakes sometimes squeal in wet weather?** | Why does thunder arrive noticeably later than the lightning flash that caused it? *(dci1/v2,dci1v3)* | restatement (named by the re-audit) |
| `b1-history-19` | history | reserved confirmatory | How did banking grow out of the habits of early merchants? | **How did public bathhouses shape daily life in ancient cities?** | Why did expanding trade push merchants to invent banking, credit, and insurance? *(dci1/v2)* | restatement (named by the re-audit) |
| `b1-music-44` | music | reserved confirmatory | Why do musical tastes often settle in early adulthood? | **Why do musicians tap a foot while playing a piece?** | Why do many people's musical tastes form in adolescence and stay stable through adulthood? *(dci1/v2,dci1v3)* | restatement (named by the re-audit) |
| `b1-sport-13` | sport | reserved confirmatory | How does a cyclist's choice of gear change the effort on a hill? | **How does a swimmer's flip turn at the wall save so much time?** | Explain how a bicycle gear changes pedalling effort. *(dci/v19/task_bank)* | restatement (named by the re-audit) |

### 3b. The other 77 replacements of 2026-10-19

| topic id | category | used in | original question | replacement | question it overlapped *(source)* | reason |
|---|---|---|---|---|---|---|
| `b1-everyday-science-42` | everyday science | Stage 1 (pilot) | Why does a whistle produce such a piercing high sound? | **Why does a teaspoon rattle in a cup on a moving train?** | Explain how a whistle produces a steady tone. *(dci/v19/task_bank)* | close to a historical question |
| `b1-geography-40` | geography | Stage 1 (pilot) | Why do fjords cut so deeply into some coastlines? | **Why do some rivers split into many channels across a plain?** | What makes fjords so distinctive, and how were they carved? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-work-and-organisations-47` | work and organisations | Stage 1 (pilot) | Why do people judge a new workplace by its first few days? | **Why do some workplaces ban emails after a certain hour?** | What makes the first weeks in a new job decisive for whether a hire stays or leaves? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-art-and-design-29` | art and design | Stage 2 (pilot) | Why do many admired paintings use only a narrow range of colours? | **Why do sign painters outline lettering in a darker colour?** | Why does a limited palette often produce stronger paintings than unlimited color choices? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-art-and-design-39` | art and design | Stage 2 (pilot) | How does the pattern of brickwork affect the strength of a wall? | **How does a cabinet maker hide the joints in a piece of furniture?** | Describe why bricklayers stagger the joints in a wall. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-art-and-design-46` | art and design | Stage 2 (pilot) | How does a tapestry differ from a painting in the way it is made? | **How does a potter centre a lump of clay on a spinning wheel?** | new question `b1-art-and-design-31`: How does a tapestry weaver build a picture thread by thread? *(new bank)* | duplicate of another new question |
| `b1-food-07` | food | Stage 2 (pilot) | Why do potatoes turn green when left out in the light? | **Why do carrots go limp after a few days in the fridge?** | Describe why potatoes are stored in the dark. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-food-45` | food | Stage 2 (pilot) | How do hours of gentle cooking make tough meat tender? | **How do cooks get crisp skin on a roast chicken?** | What makes tough, well-worked cuts turn silky in a slow braise while lean cuts dry out? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-geography-04` | geography | Stage 2 (pilot) | How do volcanic islands form far from any continent? | **How do floating islands of vegetation form on some lakes?** | How do chains of islands rise from the middle of deep oceans? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-health-and-the-body-40` | health and the body | Stage 2 (pilot) | Why does your own voice sound strange when played back? | **Why does your nose run when you breathe cold air?** *(changed again on 2026-10-25, §3c)* | Why does your recorded voice sound so unlike the voice you hear while speaking? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-language-and-writing-09` | language and writing | Stage 2 (pilot) | Why can tone of voice change the meaning of a remark? | **Why can people read text with the vowels left out?** | How can the same sentence carry very different meanings depending on tone of voice? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-the-natural-world-16` | the natural world | Stage 2 (pilot) | How do cacti survive long periods without rain? | **How do some reptiles regrow a lost tail?** | Why do desert plants often have waxy surfaces and deep roots? *(dci1v3,dci1v3/candidates)* | close to a historical question |
| `b1-art-and-design-05` | art and design | reserved confirmatory | Why do some city squares feel lively while others stay empty? | **Why do lacemakers pin their work to a cushion?** | What separates an inviting public plaza from one that people avoid? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-art-and-design-34` | art and design | reserved confirmatory | Why do art students still draw the human figure from life? | **Why do glass cutters score a pane of glass first?** | Why is drawing from direct observation still valued when photography exists? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-art-and-design-40` | art and design | reserved confirmatory | Why does the choice of frame affect how a painting is seen? | **Why does a mural painter draw a grid on the wall first?** | How does the frame around a picture influence how viewers perceive it? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-everyday-science-01` | everyday science | reserved confirmatory | How does a liquid thermometer show changes in temperature? | **How does a dehumidifier pull moisture out of room air?** | Explain how a spirit thermometer registers a change. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-everyday-science-06` | everyday science | reserved confirmatory | Why do clothes on a line dry faster on a windy day? | **Why do sticky notes lose their grip after a few uses?** | Why do puddles vanish faster on windy days even when the air stays cool? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-everyday-science-08` | everyday science | reserved confirmatory | Why does a metal bridge have small gaps built into its road surface? | **Why does a rubber ball bounce lower after a night in the cold?** | Why do bridges and railway tracks include small gaps between their long sections? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-everyday-science-13` | everyday science | reserved confirmatory | How does a siphon move water up and over the edge of a tank? | **How does a spray head turn a stream of water into a fine mist?** | Explain how a siphon moves liquid over a rim. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-everyday-science-17` | everyday science | reserved confirmatory | Why does tyre pressure drop when the weather turns cold? | **Why does a sheet of paper curl when one side gets damp?** | Why does a balloon shrink when you put it in the freezer? *(dci1v3,dci1v3/candidates)* | restatement (found by the semantic review) |
| `b1-everyday-science-18` | everyday science | reserved confirmatory | Why do sealed snack bags swell up at high altitude? | **Why does a bathtub drain swirl as the water runs out?** | Why do your ears pop when a plane climbs or a car descends a mountain? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-everyday-science-19` | everyday science | reserved confirmatory | How does a glow stick start to shine when it is bent? | **How does bending a paper clip back and forth make it snap?** | What happens inside a glow stick when you snap it and it lights up? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-everyday-science-23` | everyday science | reserved confirmatory | Why does a rolling coin stay upright longer than a still one? | **Why can a hot mug slide on its own across a wet tray?** | What keeps a spinning top balanced long after a motionless one would fall? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-everyday-science-43` | everyday science | reserved confirmatory | How does a pressure cooker cook food faster than an open pan? | **How does a dimmer switch turn down the glow of a lamp?** | How does a pressure cooker shorten cooking time? *(dci1v4)* | restatement (found by the semantic review) |
| `b1-everyday-science-45` | everyday science | reserved confirmatory | Why does a car feel hotter inside than the air outside on a sunny day? | **Why does dark tarmac feel hotter than pale paving stones on a sunny day?** | Explain how a greenhouse retains warmth for plants. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-everyday-science-47` | everyday science | reserved confirmatory | Why does a fridge magnet stay stuck to the door? | **Why does a key cut for one lock not turn another?** | Why do magnets grip a steel fridge door yet ignore an aluminum pan? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-food-00` | food | reserved confirmatory | Why does whipped cream turn into butter if beaten for too long? | **Why does a boiled potato go gluey when it is mashed too hard?** | Why does whipped cream hold its shape while poured cream does not? *(dci1v3,dci1v3/candidates)* | close to a historical question |
| `b1-food-02` | food | reserved confirmatory | Why does sugar turn brown and bitter when heated on its own? | **Why does a banana skin turn black when it is kept in the fridge?** | What happens as sugar heats past melting and slides into caramel? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-food-03` | food | reserved confirmatory | Why do chillies feel hot in the mouth even when they are cold? | **Why do some cooks add a spoonful of coffee to a chocolate cake?** | Why do chili peppers feel burning hot even though they carry no real heat? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-food-04` | food | reserved confirmatory | How does kneading turn a sticky dough smooth and stretchy? | **How does a cook stop custard from turning lumpy?** | How does kneading develop dough, and why do bakers sometimes stop early? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-food-06` | food | reserved confirmatory | How does honey stay edible for such a long time? | **How do bubbles in a crumpet leave so many holes on top?** | Explain how honey resists spoiling for long periods. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-food-10` | food | reserved confirmatory | Why do cooks add starchy cooking water to a sauce? | **Why do cooks soak wooden skewers in water first?** | Why do many cooks save the cloudy water left over from boiling pasta? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-food-12` | food | reserved confirmatory | Why does browned meat taste so different from boiled meat? | **Why does red cabbage change colour when vinegar is added?** | How does searing meat change its flavor compared with gently boiling it? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-food-19` | food | reserved confirmatory | How does churning while freezing keep ice cream smooth? | **How does a pizza stone help the crust cook evenly?** | How does ice cream stay soft and scoopable instead of freezing solid? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-food-24` | food | reserved confirmatory | How does a crisp crust form on a loaf as it bakes? | **How does a dark baking tin make a cake brown faster?** | Describe why bread crusts brown in the oven. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-food-25` | food | reserved confirmatory | Why do bakers slash the top of a loaf before it goes in the oven? | **Why do bakers brush the top of a pie with beaten egg before it goes in?** | Describe why bakeries score the tops of loaves. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-food-32` | food | reserved confirmatory | Why does tea taste bitter if it is left to brew too long? | **Why does a boiled egg peel more easily when it is a few days old?** | How do water temperature and steeping time transform the flavor of tea? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-geography-00` | geography | reserved confirmatory | How do fjords form along a mountainous coastline? | **How do meandering rivers gradually cut off loops of water?** *(changed again on 2026-10-25, §3c)* | What makes fjords so distinctive, and how were they carved? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-geography-05` | geography | reserved confirmatory | Why does daylight barely change through the year near the equator? | **Why do some beaches have black sand rather than pale sand?** | Why do polar regions swing between months of darkness and midnight sun? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-geography-10` | geography | reserved confirmatory | How do mapmakers show a round planet on a flat sheet? | **How do surveyors measure the height of a distant mountain?** | How do maps distort the world, and why must flat maps always trade something away? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-geography-13` | geography | reserved confirmatory | How do sinkholes appear so suddenly in the ground? | **How do mudflats form along sheltered estuaries?** | What makes limestone country prone to sinkholes, caves, and vanishing rivers? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-geography-18` | geography | reserved confirmatory | Why do seaside towns rarely see extreme temperatures? | **Why do many glacial lakes look unnaturally turquoise?** | Why do temperatures swing more widely in places far from the ocean? *(dci1v3,dci1v3/candidates)* | restatement (found by the semantic review) |
| `b1-geography-23` | geography | reserved confirmatory | Why do thick fogs regularly roll in along certain coasts? | **Why do dust storms sweep across certain plains each spring?** | Why do some coastal towns experience fog far more often than places inland? *(dci1v3,dci1v3/candidates)* | restatement (found by the semantic review) |
| `b1-geography-24` | geography | reserved confirmatory | Why do some places have daylight at midnight in summer? | **Why do some volcanoes erupt violently while others pour out lava?** | Why do polar regions swing between months of darkness and midnight sun? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-geography-35` | geography | reserved confirmatory | Why are mountain tops colder even though they are nearer the sun? | **Why are some mountain passes open all winter while others close with snow?** | How does climbing in altitude change the climate even close to the equator? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-geography-47` | geography | reserved confirmatory | Why are some islands still rising out of the sea? | **Why are some lakes almost perfectly round?** | How do chains of islands rise from the middle of deep oceans? *(dci1/v2)* | close to a historical question |
| `b1-health-and-the-body-01` | health and the body | reserved confirmatory | Why does yawning seem to spread from one person to another? | **Why does a paper cut sting so much more than a larger scrape?** | Why do people yawn when they see someone else yawning? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-health-and-the-body-04` | health and the body | reserved confirmatory | Why does a foot go numb after sitting cross-legged for too long? | **Why does the skin on the hands crack and bleed in cold weather?** | new question `b1-health-and-the-body-00`: What causes pins and needles in an arm or leg? *(new bank)* | duplicate of another new question |
| `b1-health-and-the-body-12` | health and the body | reserved confirmatory | How does the immune system remember an infection it has met before? | **How does the body break down a medicine and clear it from the blood?** | Describe how vaccines train immune memory in general terms. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-health-and-the-body-21` | health and the body | reserved confirmatory | How do muscles grow stronger after repeated hard use? | **How does the tongue tell sweet from sour?** | How does the body adapt over weeks when someone starts strength training? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-health-and-the-body-24` | health and the body | reserved confirmatory | Why does the body raise its temperature during an infection? | **Why does the stomach rumble noticeably before a meal is due?** | How does fever help the body fight infection even though it feels awful? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-health-and-the-body-32` | health and the body | reserved confirmatory | How does blood clot to stop a small cut from bleeding? | **How does the body make new blood after someone gives a donation?** | Why does a scab form over a cut as it heals? *(dci1v3,dci1v3/candidates)* | close to a historical question |
| `b1-health-and-the-body-39` | health and the body | reserved confirmatory | Why do some people get seasick while others are untroubled? | **Why does sunburn appear on some skin much sooner than on other skin?** | Why does motion sickness strike some travellers and spare others? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-health-and-the-body-44` | health and the body | reserved confirmatory | Why does a twisted ankle swell up? | **Why do knuckles crack when pulled?** | new question `b1-health-and-the-body-34`: Why does a bump on the head swell up so quickly? *(new bank)* | duplicate of another new question |
| `b1-history-00` | history | reserved confirmatory | How did taming the horse change how far people could travel? | **How did the sewing machine change the making of clothes at home?** | In what ways did taming horses transform how societies fought, traded, and traveled? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-history-08` | history | reserved confirmatory | Why did early railways push towns to agree on a shared clock time? | **Why did early cinemas hire musicians to play during silent films?** | How did the standardisation of time affect travel? *(dci1v4)* | close to a historical question |
| `b1-history-11` | history | reserved confirmatory | Why did castles gradually fall out of use? | **Why did town criers gradually fall out of use?** | Why did stone castles gradually lose their military value as gunpowder weapons improved? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-history-17` | history | reserved confirmatory | Why did early sailors seek new sea routes to the spice markets? | **Why did early sailors carry live animals on long voyages?** | Why were spices once so precious that nations fought wars over their trade? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-history-22` | history | reserved confirmatory | How did public sewers change life in growing cities? | **How did street numbering change the delivery of letters?** | How did clean water and sewer projects transform life in crowded industrial cities? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-history-33` | history | reserved confirmatory | How did the magnetic compass change long sea voyages? | **How did tarmac road surfaces change rural travel and trade?** | How did advances in navigation let sailors venture far beyond familiar coastlines? *(dci1/v2)* | close to a historical question |
| `b1-language-and-writing-06` | language and writing | reserved confirmatory | How does a mystery novel keep readers guessing until the end? | **How does a tongue twister trip up the person saying it?** | How do writers create suspense while still playing fair with the reader? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-language-and-writing-39` | language and writing | reserved confirmatory | Why do dictionaries keep adding new entries every year? | **Why do some languages write from right to left?** | How does a dictionary decide what to include? *(dci1v4)* | close to a historical question |
| `b1-music-01` | music | reserved confirmatory | Why do many listeners hear music in a minor key as sad? | **Why do many listeners find slow songs easier to sing along to?** | In what ways can a melody suggest sadness or joy without any lyrics at all? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-music-02` | music | reserved confirmatory | How does a flute make sound without any reed or string? | **How does a harpist keep track of so many strings at once?** | Explain how a whistle produces a steady tone. *(dci/v19/task_bank)* | close to a historical question |
| `b1-music-13` | music | reserved confirmatory | How does a pipe organ produce such a wide range of sounds? | **How does a pianist play two different rhythms with each hand?** | new question `b1-music-07`: How does a church organ make so many different sounds? *(new bank)* | duplicate of another new question |
| `b1-sport-02` | sport | reserved confirmatory | Why do racing cyclists ride so close behind one another? | **Why do cyclists shave their legs before a big race?** | How do endurance cyclists share the workload within a team during a long race? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-sport-37` | sport | reserved confirmatory | How does a golf handicap let players of different ability compete? | **How does a bowling green stay so smooth and level?** | Why do many sports use handicaps or weight classes to keep competition fair? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-technology-28` | technology | reserved confirmatory | How does a microphone capture a voice? | **How does a dashcam decide which clips to keep?** | Explain how a microphone turns sound into a signal. *(dci/v19/task_bank)* | restatement (found by the semantic review) |
| `b1-technology-31` | technology | reserved confirmatory | How does a wind turbine generate electricity? | **How does a bike dynamo power a headlamp while pedalling?** | Explain how a windmill converts wind into rotation. *(dci/v19/task_bank)* | close to a historical question |
| `b1-the-natural-world-27` | the natural world | reserved confirmatory | How do beavers change the rivers they live on? | **How do bees build such regular six-sided cells?** | How do beavers change the landscape, and who benefits from those changes? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-the-natural-world-37` | the natural world | reserved confirmatory | Why do young sunflowers turn to follow the sun? | **Why do some leaves fold up when touched?** | Why do houseplants on a windowsill gradually lean toward the glass? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-the-natural-world-41` | the natural world | reserved confirmatory | Why do some animals store food ready for winter? | **Why do some moths fly towards lamps at night?** | How do animals survive winters when food is scarce and temperatures plunge? *(dci1/v2)* | close to a historical question |
| `b1-the-natural-world-46` | the natural world | reserved confirmatory | Why are some frogs so brightly coloured? | **Why are some birds' eggs speckled?** | How does camouflage evolve, and why do some animals advertise themselves instead? *(dci1/v2,dci1v3)* | close to a historical question |
| `b1-work-and-organisations-15` | work and organisations | reserved confirmatory | Why do mentors matter so much early in a career? | **Why do shops close for a stocktake once a year?** | In what ways can a mentor shape a career more than formal training does? *(dci1/v2)* | restatement (found by the semantic review) |
| `b1-work-and-organisations-29` | work and organisations | reserved confirmatory | Why do people value recognition as much as pay? | **Why do restaurants pool tips among all the staff?** | In what ways do awards and titles motivate staff differently from money? *(dci1/v2,dci1v3)* | restatement (found by the semantic review) |
| `b1-work-and-organisations-36` | work and organisations | reserved confirmatory | Why do some companies hold their meetings standing up? | **Why do some companies close entirely for two weeks each summer?** | new question `b1-work-and-organisations-43`: Why do some organisations hold a short daily meeting standing up? *(new bank)* — since rewritten as: Why do some organisations require two signatures on large payments? | duplicate of another new question |
| `b1-work-and-organisations-43` | work and organisations | reserved confirmatory | Why do some organisations hold a short daily meeting standing up? | **Why do some organisations require two signatures on large payments?** | Why do many teams hold short daily meetings instead of long weekly ones? *(dci1v3,dci1v3/candidates)* | restatement (found by the semantic review) |

### 3c. The 26 questions rewritten on 2026-10-25 (D05 decision)

| topic id | category | used in | original question | replacement | question it overlapped *(source)* | reason |
|---|---|---|---|---|---|---|
| `b1-art-and-design-00` | art and design | Stage 1 (pilot) | How does a mosaic artist choose the size of each tile? | **How does a maze maker keep walkers lost for so long?** | How does a mosaic hold together as an image? *(dci1v4)* | restatement under the containment rule |
| `b1-history-28` | history | Stage 1 (pilot) | How did shorthand writing become a valued business skill? | **How did shorthand writing become a valued professional skill?** | — | reworded to restore an 11+-letter word in Stage 1 |
| `b1-language-and-writing-14` | language and writing | Stage 1 (pilot) | Why do some stories begin in the middle of the action? | **Why do some books get a new title in another country?** | What makes some openings of novels pull readers in immediately? *(dci1/v2)* | restatement under the containment rule |
| `b1-technology-20` | technology | Stage 1 (pilot) | How does a smartwatch estimate the steps someone takes? | **How does a smartwatch approximate the steps someone takes?** | — | reworded to restore an 11+-letter word in Stage 1 |
| `b1-health-and-the-body-40` | health and the body | Stage 2 (pilot) | Why does your nose run when you breathe cold air? | **Why does your skin bruise more easily as you get older?** | new question `b1-health-and-the-body-26`: How does the nose warm and clean air before it reaches the lungs? *(new bank)* | restatement under the containment rule |
| `b1-music-12` | music | Stage 2 (pilot) | How does a songwriter build a chorus that people remember? | **How does a backing vocalist harmonise with the lead singer?** | Why are choruses usually the part of a song that crowds sing loudest? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-work-and-organisations-04` | work and organisations | Stage 2 (pilot) | Why do some organisations ask staff to wear uniforms? | **Why do some organisations send mystery shoppers into their stores?** | In what ways do uniforms and dress codes shape behaviour at work? *(dci1/v2)* | restatement under the containment rule |
| `b1-everyday-science-14` | everyday science | reserved confirmatory | Why does an empty room produce echoes that a furnished one does not? | **Why does a shower curtain sometimes drift inwards while the hot water runs?** | How does a room change the sound of a live performance? *(dci1v4)* | restatement under the containment rule |
| `b1-everyday-science-24` | everyday science | reserved confirmatory | Why do aeroplanes leave white trails across a clear sky? | **Why do old newspapers turn yellow as the years pass?** | Why can you see your breath on a cold morning but not in summer? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-everyday-science-30` | everyday science | reserved confirmatory | Why can water freezing in a pipe split the pipe open? | **Why does a frozen lake sometimes make strange singing noises?** | Describe why potholes form after a cold winter. *(dci/v19/task_bank)* | restatement under the containment rule |
| `b1-everyday-science-39` | everyday science | reserved confirmatory | Why does painted wood fade after years in strong sunshine? | **Why does a metal tape measure stay rigid when extended?** | Describe why museums dim the lights near old textiles. *(dci/v19/task_bank)* | restatement under the containment rule |
| `b1-food-14` | food | reserved confirmatory | Why does a pinch of salt make sweet foods taste sweeter? | **Why does cooked spinach shrink to almost nothing in the pan?** | How does salt do far more in cooking than simply making dishes salty? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-food-16` | food | reserved confirmatory | How does milk turn into yoghurt? | **How does coffee lose its caffeine?** | What gives fermented foods like yogurt and kimchi their distinctive tang? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-food-17` | food | reserved confirmatory | Why are mushrooms so rich in savoury flavour? | **Why are pistachio shells often already split open?** | Why do cooks treat savory umami as a taste of its own, and which foods supply it richly? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-food-36` | food | reserved confirmatory | How does curing turn a leg of pork into ham? | **How does a wok give food that smoky charred taste?** | Why are some hams and cheeses aged for years, and what changes during the wait? *(dci1/v2)* | restatement under the containment rule |
| `b1-food-43` | food | reserved confirmatory | Why do some cooks salt aubergines before frying them? | **Why do some cooks bruise lemongrass before adding it?** | How does salt change the texture of vegetables as they cook? *(dci1v4)* | restatement under the containment rule |
| `b1-geography-00` | geography | reserved confirmatory | How do meandering rivers gradually cut off loops of water? | **How do scientists read past climates from layers of lake mud?** | How does the course of a river change over time? *(historical)* | restatement under the containment rule |
| `b1-health-and-the-body-08` | health and the body | reserved confirmatory | Why does laughing make people feel good? | **Why does the voice crack during emotional moments?** | How does laughter affect the body beyond simply lifting the mood? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-history-05` | history | reserved confirmatory | How did the spread of reading among ordinary people change society? | **How did the rise of seaside holidays change coastal towns?** | How did the spread of printing change who could join public debate? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-language-and-writing-13` | language and writing | reserved confirmatory | How does sarcasm work when the listener has only the voice to go on? | **How does a person learn to lip read when they cannot hear the speaker?** | What happens to meaning when sarcasm moves from speech to text? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-language-and-writing-40` | language and writing | reserved confirmatory | How does an author decide how a story should end? | **How does a writer of radio plays set a scene?** | What makes an ending feel earned rather than abrupt in a piece of fiction? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-language-and-writing-46` | language and writing | reserved confirmatory | Why do people from neighbouring regions often struggle to understand each other's speech? | **Why do historians place a full bibliography at the back of their books?** | How do regional dialects develop within a single shared language? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-music-04` | music | reserved confirmatory | How does an unaccompanied choir stay in tune? | **How does piano accompaniment support a nervous soloist?** | What happens to a choir's sound when singers listen closely to one another rather than to themselves? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-technology-40` | technology | reserved confirmatory | How does a parking sensor judge the distance to a wall? | **How does a digital kitchen scale measure the weight of flour?** | How do sensors in a modern car help drivers avoid collisions? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-work-and-organisations-14` | work and organisations | reserved confirmatory | How does a team handle disagreement between two capable members? | **How does a gym keep members paying their monthly subscription?** | What makes some teams argue productively while others just argue? *(dci1/v2,dci1v3)* | restatement under the containment rule |
| `b1-work-and-organisations-20` | work and organisations | reserved confirmatory | Why do some firms give candidates a trial project before hiring them? | **Why do some firms allow employees to bring dogs into the workplace?** | What makes a job interview a poor predictor of how someone will actually perform? *(dci1/v2,dci1v3)* | restatement under the containment rule |

<!-- END GENERATED -->

## 4. How the replacements were checked

| check | what it catches | result |
|---|---|---|
| **exact and sequestered match** | a historical question copied word for word, including the v3 and v4 questions only kept as hashes | 0 |
| **word-overlap screen** (two Jaccard similarities, as before) | close rewordings | every flagged pair reviewed |
| **rare-word screen** (new) | two questions sharing two or more unusual words, such as *popcorn* and *burst*. "Unusual" means at most 6 of the 2,048 questions use the word | every flagged pair reviewed; 59 recorded decisions in total |
| **semantic review, first pass** | restatements that share no unusual words | 60 restatements, 6 duplicate pairs, 87 close |
| **semantic review, second pass** | whether a replacement is itself a restatement or a duplicate | 88 replacements: 0 restatements, 0 duplicates, 5 close, 1 wording problem |
| **third pass** | the questions changed after the second pass | 3 checked independently (0 problems; one close pair fixed); 5 small rewordings checked only by the author |
| **form and instruction check** | a question that is not one plain question, contains an instruction, or uses a word the instructions require or forbid (*indeed*, *simple*, *very*…) | clean |
| **balance check** | replacements systematically easier or harder | see below |

**Semantic review method.** Each reviewer read the full historical list and
its quarter of the bank. For each question it saw the eight most
word-similar historical questions as hints, and it was told to look beyond
them. It classified each question as a restatement ("a good answer to one
would largely answer the other"), close, or neither. The second-pass
reviewer read both full lists and judged only the 88 replacements. The
reviewers are AI models, not people; they are useful because they read for
meaning, but they are not a substitute for your review. The full record,
one line per finding, is
[`src/dci/batch1/data/topics_semantic_review.json`](../../src/dci/batch1/data/topics_semantic_review.json).
The overlap check refuses the bank while any question marked as a
restatement is still in it.

**Balance.** Topic wording can change how hard an instruction is: answers
reuse the question's words, so a long word in the question makes the word
length limit B harder, and the letters *b* and *z* matter for the two
letter prohibitions. The replacements were written to match the questions
they replace:

| feature | 88 original questions | 88 replacements |
|---|---|---|
| mean words | 10.51 | 10.74 |
| mean longest word (letters) | 8.18 | 7.83 |
| longest word of 9 or more letters | 32 | 31 |
| contains the letter b | 30 | 30 |
| contains the letter z | 1 | 1 |
| same opening word ("Why"/"How") | — | 88 of 88 |

Pilot profiles before and after (the Stage 1 and Stage 2 sets are what the
pilot measures):

| set | mean longest word, before → after | longest ≥ 11 letters | contains b | "Why" questions |
|---|---|---|---|---|
| Stage 1 (32) | 8.09 → 7.91 | 0.09 → 0.03 | 0.41 → 0.41 | 0.50 → 0.50 |
| Stage 2 (64) | 8.22 → 8.19 | 0.05 → 0.05 | 0.41 → 0.41 | 0.39 → 0.39 |
| reserved (480) | 8.35 → 8.30 | 0.12 → 0.11 | 0.41 → 0.41 | 0.49 → 0.49 |

The one visible shift is in Stage 1: two fewer questions with an 11-letter
word (3 of 32 → 1 of 32). That makes B very slightly easier on Stage 1
topics than before. It is small, and Freeze 2 already reports a
Stage-1-only sensitivity, but you may prefer to restore a long word in one
or two Stage 1 replacements. Nothing here reads model behaviour: these are
properties of the question text only.

## 5. Validation summary and remaining concerns

**Validated (all automatic checks run on 2026-10-19):**

- the overlap report is clean: 2,096 historical records from 7 sources and
  192 sequestered hashes; 0 exact or sequestered matches; every flagged pair
  reviewed; no recorded restatement left in the bank;
- form and instruction checks are clean;
- the split is unchanged: the same 32, 64 and 480 topic ids, as a test
  confirms by restoring the old questions;
- tests in `tests/batch1/test_topics.py` (27 pass) check the rare-word screen,
  the semantic-review gate, that the 11 named questions were rewritten and
  would be refused if restored, and that replacements keep id, category and
  opening word.

**Remaining concerns:**

1. **The semantic review was done by AI reviewers.** They found everything
   the re-audit found, but a restatement that both missed is possible. The
   strongest protection is your own reading of §3.
2. **The bank as a whole was written by an AI agent and is unreviewed.** This
   review covers its independence from history, not whether every question
   is a good topic.
3. **67 "close" questions were kept.** Each shares a subject with a
   historical question but asks something different. If you prefer a stricter
   line, the list is in `topic_screen_report.md` and any of them can be
   rewritten the same way.
4. **Five small rewordings were checked only by the author**
   (`b1-food-10`, `b1-health-and-the-body-39`, `b1-history-33`,
   `b1-everyday-science-19`, `b1-food-24`), against both full lists.
5. **The share of rewritten questions is large (88 of 576).** The bank was
   drafted from the same everyday subjects the historical banks used. Some
   remaining questions sit near historical subjects without restating them.

## 6. Files to inspect

| file | what it is |
|---|---|
| [`src/dci/batch1/data/topics_source.json`](../../src/dci/batch1/data/topics_source.json) | the bank: 576 questions, plus every revision with its previous text, reason and the question it overlapped |
| [`src/dci/batch1/data/topics_semantic_review.json`](../../src/dci/batch1/data/topics_semantic_review.json) | the semantic review record (all three passes) |
| [`src/dci/batch1/data/topics_review.json`](../../src/dci/batch1/data/topics_review.json) | the screen's reviewed pairs, each bound to both questions' text |
| [`topic_screen_report.md`](topic_screen_report.md) | generated: every revision, every reviewed pair, every kept "close" question, and the set profiles |
| [`topic_overlap.json`](topic_overlap.json), [`topic_hygiene.json`](topic_hygiene.json), [`topic_split.json`](topic_split.json) | generated machine-readable reports and the split |
| [`src/dci/batch1/topics.py`](../../src/dci/batch1/topics.py) | the screens and the split |

## 7. What approving D05 means

Approving D05 approves the allocation (32 topics in Stage 1, 64 in Stage 2,
96 in total) **and this exact bank, split and review record**: the D05
payload binds the bank hash, the split hash, the screen settings and the
hashes of both review files. Changing any question later voids the approval,
and Freeze 1 would have to be redone.
