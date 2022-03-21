# Book SFC skill (DFF)
This is an SFC-customized Book Skill service that discusses books with the user. Unlike the original Book Skill, this Skill has been augmented with the Speech Function classifier and predictor.

# Example of using SFs in DFF DSL
In this version, you can see how conditions based on speech functions can be used for transition to desired nodes. <br> 

To see how SFs can be used as conditions for transition to the next node, check out:

```/skills/dff_book_sfc_skill/scenario/main.py```, [line #234](https://github.com/deepmipt/dream/blob/feat/sf-bookskill-new/skills/dff_book_sfc_skill/scenario/main.py#L234)

To see how to specify an SF of a bot's utterance to be able to make predictions for this utterance, check out:

```/skills/dff_book_sfc_skill/scenario/main.py```, [line #239](https://github.com/deepmipt/dream/blob/feat/sf-bookskill-new/skills/dff_book_sfc_skill/scenario/main.py#L239)

# All SFs available for use
Here is a list of all speech functions available for use in this version: <br>

 | SF | Explanation | Example |
 | --- | --- | --- |
 | Open.Attend | These are usually greetings. NB: Used in  the beginning of a conversation. | Hi! <br>Hello! <br>Good morning! <br>Hey, Steve! |
 | Open.Demand.Fact | Demanding factual information. NB: Used in  the beginning of a conversation. | What’s Allenby doing these days? |
 | Open.Demand.Opinion | Demanding judgment or evaluative information from the interlocutor. NB: Used in  the beginning of a conversation. | What do you think about it? <br>Do you like your new job? |
 | Open.Give.Fact | Providing factual information. NB: Used in  the beginning of a conversation. |  I met his sister. |
 | Open.Give.Opinion | Providing judgment or evaluative information. NB: Used in  the beginning of a conversation. | This conversation needs Allenby. <br>It was too boring. |
 | React.Rejoinder.Confront.Challenge.Counter | The speaker expresses disagreement with the statement of another, denies the importance, reliability or relevance of the statement of his interlocutor. | Nick: He is so good at music. <br> **David: You don't understand, Nick.** |
 | React.Rejoinder.Confront.Challenge.Rebound | Questioning the relevance, reliability of the previous statement, most often an interrogative sentence. | David: This conversation needs Allenby.<br>**Fay: Oh he’s in London.** So what can we do? |
 | React.Rejoinder.Confront.Response.Re-challenge | Offering an alternative position, often an interrogative sentence. | David: Messi is the best.<br>**Nick: Maybe Pele is the best one?** |
 | React.Rejoinder.Support.Response.Resolve | The response provides the information requested in the question. | Nick: When will she arrive?<br>Fay: Tommorow.<br>Lina: What do you think of this song?<br>**Fay: I really like its lyrics.** |
 | React.Rejoinder.Support.Track.Check | Getting the previous speaker to repeat an element or the entire statement that the speaker has not heard or understood. | Straight into the what?<br>What do you mean? |
 | React.Rejoinder.Support.Track.Clarify | Asking a question to get additional information on the current topic of the conversation. Requesting to clarify the information already mentioned in the dialog. | What, before bridge? |
 | React.Rejoinder.Support.Track.Confirm | Asking for a confirmation of the information received.  | David: Well, he rang Roman, he rang Roman a week ago.<br>**Nick: Did he?** |
 | React.Rejoinder.Support.Track.Probe | Requesting a confirmation of the information necessary to make clear the previous speaker's statement. The speaker themselves speculates about the information that they want to be confirmed.  | Because Roman lives in Denning Road also? |
 | React.Respond.Confront.Reply.Contradict | Refuting previous information. No, sentence with opposite polarity. If the previous sentence is negative, then this sentence is positiv, and vice versa. NB! The speaker contradicts the information that he already knew before. | Fay: Suppose he gives you a hard time, Nick?<br>**Nick: Oh I like David a lot.** |
 | React.Respond.Confront.Reply.Disagree | Negative answer to a question or denial of a statement. No, negative sentence. <br> | Fay: David always makes a mess in our room. <br>**May: No, he's not so bad.** |
 | React.Respond.Confront.Reply.Disawow | Denial of knowledge or understanding of information. | I don’t know.<br>No idea. |
 | React.Respond.Support.Develop.Elaborate | Clarifying / rephrasing the previous statement or giving examples to it. A declarative sentence or phrase (may include for example, I mean, like).  | Nick: Cause all you’d get is him bloody raving on.<br>**Fay: He’s a bridge player, a naughty bridge player.** |
 | React.Respond.Support.Develop.Enhance | Adding details to the previous statement, adding information about time, place, reason, etc. A declarative sentence or phrase (may include then, so, because). | Fay: He kept telling me I’ve got a big operation on with<br>**Nick: The trouble with Roman though is that — you know he does still like cleaning up.** |
 | React.Respond.Support.Develop.Extend | Adding supplementary or contradictory information to the previous statement. A declarative sentence or phrase (may include and, but, except, on the other hand). | David: That’s what the cleaner — your cleaner lady cleaned my place thought<br>**Nick: She won’t come back to our place.** |
 | React.Respond.Support.Engage | Drawing attention or a response to a greeting? |  Hi! <br> Hey, David. |
 | React.Respond.Support.Register | A manifestation of emotions or a display of attention to the interlocutor. | Yeah.<br> Right.<br> Hmm... |
 | React.Respond.Support.Reply.Acknowledge | Indicating knowledge or understanding of the information provided. | I know.<br>I see. |
 | React.Respond.Support.Reply.Affirm | A positive answer to a question or confirmation of the information provided. Yes/его synonyms or affirmation. NB! The speaker confirms the information that he already knew before. | Nick: He went to London.<br>**Fay: He did.** |
 | React.Respond.Support.Reply.Agree | Agreement with the information provided. In most cases, the information that the speaker agrees with is new to him. Yes/its synonyms or affirmation. | Steve: We're gonna make it.<br>**Mike: Yeah, right.** |
 | Sustain.Continue.Monitor | Checking the involvement of the listener or trying to pass on the role of speaker to them. | You met his sister that night we were doing the cutting and pasting up. **Do you remember?** |
 | Sustain.Continue.Prolong.Elaborate | Clarifying / rephrasing the previous statement or giving examples to it. A declarative sentence or phrase (may include for example, I mean, like). | Dave: Yeah but I don’t like people… um... **I don’t want to be INVOLVED with people.** |
 | Sustain.Continue.Prolong.Enhance | Adding details to the previous statement, adding information about time, place, reason, etc. A declarative sentence or phrase (may include then, so, because). | David: Nor for much longer. **We’re too messy for him.** |
 | Sustain.Continue.Prolong.Extend | Adding supplementary or contradictory information to the previous statement. A declarative sentence or phrase (may include and, but, except, on the other hand). | Nick: Just making sure you don’t miss the boat. **I put it out on Monday mornings. I hear them. I hate trucks.** |

# Metrics

OS: Windows 10
CPU: AMD Ryzen 5 3500U @ 2.10GHz

| Metric       | Average value |
| ------------ | ------------- |
| RAM          | ~ 385 MB      |
| Startup time | ~  3.985s     |
| Execute time | ~  2.687s     |
