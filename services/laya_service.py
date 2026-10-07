from laya import Router

router = Router()

def handle_decision(query: str):
    state = {"body": query}
    questions = {
        "department": {
            "type": "choice",
            "instructions": "Route this customer message to the right team.",
            "criteria": {
                "faq": "prices, menu, opening hours, location, payment methods, credit cards, general restaurant info",
                "reservation": "booking, changing or cancelling a table, date, time, party size, availability",
            },
        }
    }

    result = router.predict(state, questions)

    return {
        "query": state,
        "answer": result
    }