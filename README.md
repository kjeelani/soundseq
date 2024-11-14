# SoundSeq
## Introduction
SoundSeq is a prototype for an AI-powered SFX Sequencer that can automatically apply relevant sound effects at the right places given a video. It won Most Impressive Technical Feat in Pear x OpenAI's Hackathon!

## Use Cases
We see this being useful for:
1) batch automation of content creation (i.e reels or shorts)
2) Independent film creators and animators (SFX can take an upwards of 3 hours to find and place sounds)
3) Dynamic SFX generation within games

## Architecture Diagram
![image](https://github.com/user-attachments/assets/d5403fcd-e5af-42a2-8b50-e7213aea69e5)

1) The inputted video is broken up into scenes through a simple scene detection algorithm
2) Then we grab 4 keyframes per scene and arrange it into a "comic panel" to allow GPT Vision to understand the underlying action
3) We have another LLM layer to determine what SFX best fits this action
4) We then match the given SFX descriptions to a RAG (Voyage.ai) containing a curated selection of SFX

## Future Steps

1) Curate a far larger set of SFX with better tagging using web scraping on Freesounds
2) Implement more granularity (such as asking GPT-V WHICH of the four keyframes requires SFX, or using a more real-time captioning model like Vid2Seq)
3) Employ a generative SFX model to deal with cases when there are no good matches in our RAG (or potentially even replace our RAG approach)


