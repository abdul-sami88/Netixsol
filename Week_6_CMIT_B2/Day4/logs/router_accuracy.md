# Router accuracy report

**Accuracy: 20/20 = 100%**

| Query | Expected | Predicted | Confidence | Result |
|---|---|---|---|---|
| who will win Collingwood vs Geelong this week | prediction_match | prediction_match | 0.80 | ✅ |
| will the Pies beat the Cats this week | prediction_match | prediction_match | 0.80 | ✅ |
| who's going to win the Carlton v Essendon game | prediction_match | prediction_match | 0.80 | ✅ |
| predict the winner of Richmond vs Hawthorn | prediction_match | prediction_match | 0.80 | ✅ |
| what are the chances of Fremantle winning next round | prediction_match | prediction_match | 0.80 | ✅ |
| who will top-score for Collingwood this week | prediction_player | prediction_player | 0.80 | ✅ |
| who is the best player likely to top score for the Cats | prediction_player | prediction_player | 0.80 | ✅ |
| who's the leading goalkicker going to be for Sydney | prediction_player | prediction_player | 0.80 | ✅ |
| what were Collingwood's stats last round | retrieval | retrieval | 0.75 | ✅ |
| how many disposals did Geelong average last round | retrieval | retrieval | 0.75 | ✅ |
| what was Geelong's ladder position last round | retrieval | retrieval | 0.75 | ✅ |
| how many tackles did the Cats get last round | retrieval | retrieval | 0.75 | ✅ |
| what's the highest attendance in AFL grand final history | factual | factual | 0.55 | ✅ |
| who has won the most brownlow medals | factual | factual | 0.55 | ✅ |
| explain the AFL finals system | factual | factual | 0.55 | ✅ |
| what's the weather like today | off_topic | off_topic | 0.90 | ✅ |
| can you write me some python code | off_topic | off_topic | 0.90 | ✅ |
| what's the capital of France | off_topic | off_topic | 0.90 | ✅ |
| tell me a joke | off_topic | off_topic | 0.90 | ✅ |
| predict the exact final score of Collingwood vs Geelong | unsupported | unsupported | 0.75 | ✅ |