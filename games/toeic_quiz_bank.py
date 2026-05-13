from __future__ import annotations

import random


def _shuffle_question(
    rng: random.Random,
    prompt: str,
    answer: str,
    distractors: list[str],
    category: str,
    explanation: str,
    qid: str,
) -> dict:
    choices = [answer, *distractors]
    rng.shuffle(choices)
    return {
        "id": qid,
        "category": category,
        "prompt": prompt,
        "choices": choices,
        "answer_index": choices.index(answer),
        "explanation": explanation,
    }


def build_toeic_question_bank() -> list[dict]:
    rng = random.Random(20260513)
    bank: list[dict] = []

    vocabulary_questions = [
        (
            "The manager asked everyone to submit the report by Friday.",
            "turn in",
            ["look after", "set up", "take off"],
            "vocabulary",
            "`submit` means to hand something in officially.",
            "vocab-1",
        ),
        (
            "We need to purchase new office equipment this month.",
            "buy",
            ["repair", "borrow", "display"],
            "vocabulary",
            "`purchase` is a formal way to say `buy`.",
            "vocab-2",
        ),
        (
            "Please notify the staff if the meeting time changes.",
            "inform",
            ["replace", "invite", "divide"],
            "vocabulary",
            "`notify` means to inform someone.",
            "vocab-3",
        ),
        (
            "The company will expand its service to other cities.",
            "grow",
            ["delay", "hide", "measure"],
            "vocabulary",
            "`expand` means to grow larger.",
            "vocab-4",
        ),
        (
            "All applicants must attach a resume to the form.",
            "job history",
            ["train ticket", "sales poster", "office key"],
            "vocabulary",
            "A `resume` is a document about your work history and skills.",
            "vocab-5",
        ),
        (
            "The supervisor praised her efficient work style.",
            "productive",
            ["careless", "expensive", "colorful"],
            "vocabulary",
            "`efficient` means working well without wasting time or effort.",
            "vocab-6",
        ),
        (
            "Customers may request a refund within seven days.",
            "money back",
            ["extra discount", "free delivery", "new password"],
            "vocabulary",
            "A `refund` is money returned after a purchase.",
            "vocab-7",
        ),
        (
            "The shipment arrived earlier than expected.",
            "delivery",
            ["conference", "document", "schedule"],
            "vocabulary",
            "`shipment` refers to goods that are sent somewhere.",
            "vocab-8",
        ),
        (
            "Our branch will relocate to a larger building next year.",
            "move",
            ["close permanently", "hire more staff", "raise prices"],
            "vocabulary",
            "`relocate` means to move to a new place.",
            "vocab-9",
        ),
        (
            "Please keep the receipt for your records.",
            "proof of purchase",
            ["meal ticket", "business card", "job offer"],
            "vocabulary",
            "A `receipt` shows that you bought something.",
            "vocab-10",
        ),
        (
            "The agreement will remain valid for one year.",
            "effective",
            ["secret", "damaged", "optional"],
            "vocabulary",
            "`valid` means officially acceptable or effective.",
            "vocab-11",
        ),
        (
            "He was promoted to regional sales director.",
            "given a higher position",
            ["sent home early", "moved overseas", "asked to resign"],
            "vocabulary",
            "`promoted` means advanced to a better job or rank.",
            "vocab-12",
        ),
    ]
    for prompt, answer, distractors, category, explanation, qid in vocabulary_questions:
        bank.append(_shuffle_question(rng, prompt, answer, distractors, category, explanation, qid))

    grammar_questions = [
        (
            "If you have any questions, please _____ me by email.",
            "contact",
            ["contacts", "contacting", "contacted"],
            "grammar",
            "After `please`, use the base form: `please contact`.",
            "gram-1",
        ),
        (
            "The meeting was canceled _____ the manager was ill.",
            "because",
            ["although", "unless", "during"],
            "grammar",
            "`because` gives the reason.",
            "gram-2",
        ),
        (
            "All employees must wear their ID cards _____ all times.",
            "at",
            ["for", "by", "from"],
            "grammar",
            "The fixed expression is `at all times`.",
            "gram-3",
        ),
        (
            "Ms. Tanaka is responsible _____ training new staff.",
            "for",
            ["to", "with", "about"],
            "grammar",
            "The pattern is `responsible for`.",
            "gram-4",
        ),
        (
            "The new software is easier to use _____ the old system.",
            "than",
            ["that", "then", "as"],
            "grammar",
            "Comparisons use `than`.",
            "gram-5",
        ),
        (
            "By the time we arrived, the presentation had already _____.",
            "started",
            ["start", "starting", "starts"],
            "grammar",
            "Past perfect takes the past participle: `had started`.",
            "gram-6",
        ),
        (
            "Neither the manager nor the assistants _____ available.",
            "were",
            ["was", "be", "been"],
            "grammar",
            "With `neither ... nor`, the verb often agrees with the nearer plural noun here: `assistants were`.",
            "gram-7",
        ),
        (
            "We look forward to _____ with you again.",
            "working",
            ["work", "worked", "works"],
            "grammar",
            "`look forward to` is followed by a gerund: `working`.",
            "gram-8",
        ),
        (
            "The brochure provides information _____ local attractions.",
            "about",
            ["between", "onto", "upon"],
            "grammar",
            "The natural collocation is `information about`.",
            "gram-9",
        ),
        (
            "This product is one of the most _____ options on the market.",
            "reliable",
            ["rely", "reliability", "reliably"],
            "grammar",
            "After `most`, we need an adjective: `reliable`.",
            "gram-10",
        ),
        (
            "The report should be completed _____ Monday morning.",
            "by",
            ["since", "among", "beneath"],
            "grammar",
            "`by Monday morning` means no later than that time.",
            "gram-11",
        ),
        (
            "Our clients expect orders to be processed quickly and _____.",
            "accurately",
            ["accurate", "accuracy", "accidental"],
            "grammar",
            "This modifies `processed`, so we need the adverb `accurately`.",
            "gram-12",
        ),
    ]
    for prompt, answer, distractors, category, explanation, qid in grammar_questions:
        bank.append(_shuffle_question(rng, prompt, answer, distractors, category, explanation, qid))

    business_questions = [
        (
            "What does `ASAP` mean in business email?",
            "as soon as possible",
            ["at the same price", "all staff and partners", "after sales action plan"],
            "business",
            "`ASAP` is the common abbreviation for `as soon as possible`.",
            "biz-1",
        ),
        (
            "Which phrase is best to end a polite business email?",
            "Best regards,",
            ["Wait a minute,", "Long time no see,", "No problem at all,"],
            "business",
            "`Best regards,` is a standard polite closing.",
            "biz-2",
        ),
        (
            "A `deadline` is the _____ for finishing something.",
            "final time",
            ["meeting room", "payment method", "job interview"],
            "business",
            "A `deadline` is the latest allowed time.",
            "biz-3",
        ),
        (
            "If a customer is `satisfied`, the customer is _____.",
            "pleased",
            ["confused", "absent", "delayed"],
            "business",
            "`satisfied` means pleased or content.",
            "biz-4",
        ),
        (
            "Which word best completes this phrase: `place an _____`?",
            "order",
            ["arrival", "invoice", "opinion"],
            "business",
            "The common business phrase is `place an order`.",
            "biz-5",
        ),
        (
            "A `conference call` is a call with _____.",
            "multiple participants",
            ["one delivery driver", "only customers", "no schedule"],
            "business",
            "A conference call includes several people.",
            "biz-6",
        ),
        (
            "An `invoice` is usually sent to request _____.",
            "payment",
            ["an interview", "a vacation", "a password"],
            "business",
            "An invoice asks a customer to pay.",
            "biz-7",
        ),
        (
            "Which expression means `to cancel a reservation`?",
            "call it off",
            ["fill it out", "bring it up", "hand it in"],
            "business",
            "`call it off` means cancel it.",
            "biz-8",
        ),
        (
            "A `supplier` provides goods or services to a _____.",
            "business",
            ["newspaper", "lecture", "rainstorm"],
            "business",
            "Suppliers sell or provide things to companies.",
            "biz-9",
        ),
        (
            "If sales `increased`, they _____.",
            "went up",
            ["were hidden", "stopped early", "became free"],
            "business",
            "`increase` means to go up.",
            "biz-10",
        ),
        (
            "What is the opposite of `accept an offer`?",
            "decline an offer",
            ["print an offer", "wrap an offer", "borrow an offer"],
            "business",
            "`decline` means refuse.",
            "biz-11",
        ),
        (
            "A `candidate` for a job is a person who is _____.",
            "applying",
            ["retiring", "complaining", "shipping boxes"],
            "business",
            "A job candidate is someone applying for the job.",
            "biz-12",
        ),
    ]
    for prompt, answer, distractors, category, explanation, qid in business_questions:
        bank.append(_shuffle_question(rng, prompt, answer, distractors, category, explanation, qid))

    return bank


TOEIC_QUESTION_BANK = build_toeic_question_bank()
