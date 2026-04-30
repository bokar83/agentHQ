"""
templates/email/cold_outreach.py
=================================
SINGLE SOURCE OF TRUTH for the cold outreach email.

TO UPDATE THE TEMPLATE: edit this file only.
  - Change BODY, SUBJECT, or SIGNATURE as needed.
  - Do NOT change the variable names -- everything imports by name.
  - Do NOT copy this text into any other file, crew, or agent prompt.

All tools call this file:
  from templates.email.cold_outreach import SUBJECT, BODY
"""

SUBJECT = "Where is your margin actually going?"

BODY = """Hi {first_name},

Most businesses aren't losing margin to bad strategy. They're losing it to one bottleneck: a handoff, an approval loop, a pricing gap quietly taxing everything downstream.

The frustrating part: it's almost always findable. And almost always fixable faster than people expect.

I'm Boubacar Barry, founder of Catalyst Works. I spent 15 years working with leadership teams across three continents watching the same pattern repeat: the thing slowing the business down is rarely what anyone is looking at.

What I do differently: I don't hand you a report. I find the constraint and build a clear, executable path to removing it. One that the people running the business can actually use without me in the room.

One question before I ask for anything:

Is there a place in your operation right now where work slows down or disappears that you haven't been able to fully fix?

If yes, worth a reply.

Boubacar
catalystworks.consulting"""
