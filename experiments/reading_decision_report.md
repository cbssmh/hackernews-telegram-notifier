# Reading Decision PoC Report

Generated: 2026-06-30T13:53:34+00:00

This report captures the actual outputs from the isolated reading decision experiment. It does not rank the methods or conclude which output is best.

## Personal engineering blog

Article URL: https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/

Extraction succeeded: True
Extraction time seconds: 0.48
Extracted title: Things You Should Never Do, Part I

### Output A: Title only

Word count: 7

```text
Things You Should Never Do, Part I
```

### Output B: Title + meta description

Word count: 11

```text
Things You Should Never Do, Part I

(meta description not available)
```

### Output C: Title + first meaningful paragraph

Word count: 61

```text
Things You Should Never Do, Part I

Netscape 6.0 is finally going into its first public beta. There never was a version 5.0. The last major release, version 4.0, was released almost three years ago. Three years is an awfully long time in the Internet world. During this time, Netscape sat by, helplessly, as their market share plummeted.
```

### Output D: Title + LSA extractive summary

Word count: 48

```text
Things You Should Never Do, Part I

And here is the interesting observation: they are probably wrong. There’s nothing wrong with it. When programmers say that their code is a holy mess (as they always do), there are three kinds of things that are wrong with it.
```

### Output E: Title + LexRank summary

Word count: 58

```text
Things You Should Never Do, Part I

There’s a subtle reason that programmers always want to throw away the code and start over. The reason is that they think the old code is a mess. But we did it carefully, with our existing code base, and we didn’t introduce new bugs or throw away working code.
```

### Output F: Title + TextRank summary

Word count: 96

```text
Things You Should Never Do, Part I

The reason is that they think the old code is a mess. As a corollary of this axiom, you can ask almost any programmer today about the code they are working on. “It’s a big hairy mess,” they will tell you. “I’d like nothing better than to throw it out and start over.” Why is it a mess? “Well,” they say, “look at this function. But we did it carefully, with our existing code base, and we didn’t introduce new bugs or throw away working code.
```

## Company engineering blog

Article URL: https://github.blog/engineering/architecture-optimization/how-we-improved-push-processing-on-github/

Extraction succeeded: True
Extraction time seconds: 0.315
Extracted title: How we improved push processing on GitHub

### Output A: Title only

Word count: 7

```text
How we improved push processing on GitHub
```

### Output B: Title + meta description

Word count: 11

```text
How we improved push processing on GitHub

(meta description not available)
```

### Output C: Title + first meaningful paragraph

Word count: 45

```text
How we improved push processing on GitHub

Pushing code to GitHub is one of the most fundamental interactions that developers have with GitHub every day. Read how we have significantly improved the ability of our monolith to correctly and fully process pushes from our users.
```

### Output D: Title + LSA extractive summary

Word count: 147

```text
How we improved push processing on GitHub

While most of the dozens of tasks in this job rescued all errors, for historical reasons, a few pieces of work in the beginning of the job did not. What did we do about this? We used the following approach: - We added a new Kafka topic that we publish an event to for each push. - We examined each of the many push processing tasks and grouped them by owning service and/or logical relationships (for example, order dependency, retry-ability). - For each coherent group of tasks, we placed them into a new background job with a clear owner and appropriate retry configuration. - Finally, we configured these jobs to be enqueued for each publish of the new Kafka event. - To do this, we used an internal system at GitHub that facilitates enqueueing background jobs in response to Kafka events via independent consumers.
```

### Output E: Title + LexRank summary

Word count: 58

```text
How we improved push processing on GitHub

How we improved push processing on GitHub Pushing code to GitHub is one of the most fundamental interactions that developers have with GitHub every day. What happens when you push to GitHub? Conclusion Pushing code to GitHub is one of the most fundamental interactions that developers have with GitHub every day.
```

### Output F: Title + TextRank summary

Word count: 58

```text
How we improved push processing on GitHub

How we improved push processing on GitHub Pushing code to GitHub is one of the most fundamental interactions that developers have with GitHub every day. What happens when you push to GitHub? This job was the home for all push processing logic, and its size and complexity led to many problems.
```

## Hacker News article

Article URL: https://europeancorrespondent.com/en/r/the-us-ambassador-had-belgian-police-stop-our-reporting

Extraction succeeded: True
Extraction time seconds: 3.147
Extracted title: The US ambassador had Belgian police stop our reporting

### Output A: Title only

Word count: 9

```text
The US ambassador had Belgian police stop our reporting
```

### Output B: Title + meta description

Word count: 13

```text
The US ambassador had Belgian police stop our reporting

(meta description not available)
```

### Output C: Title + first meaningful paragraph

Word count: 61

```text
The US ambassador had Belgian police stop our reporting

On Sunday evening, the United States held its “Freedom 250” celebration – paid for by private companies, organised by the three American embassies in Brussels to mark the 250th anniversary of the United States. It took place in Parc du Cinquantenaire – the city's largest park, a few hundred metres from the European Commission.
```

### Output D: Title + LSA extractive summary

Word count: 38

```text
The US ambassador had Belgian police stop our reporting

We went there to cover it. It is unclear who exactly paid how much for the party. It is unclear how much the embassy paid for renting the park.
```

### Output E: Title + LexRank summary

Word count: 84

```text
The US ambassador had Belgian police stop our reporting

The US ambassador had Belgian police stop our reporting On Sunday evening, the United States held its “Freedom 250” celebration – paid for by private companies, organised by the three American embassies in Brussels to mark the 250th anniversary of the United States. It is unclear whether the police presence that removed us was paid for by the American organisers or by Belgian taxpayers. It is unclear how much the embassy paid for renting the park.
```

### Output F: Title + TextRank summary

Word count: 93

```text
The US ambassador had Belgian police stop our reporting

The US ambassador had Belgian police stop our reporting On Sunday evening, the United States held its “Freedom 250” celebration – paid for by private companies, organised by the three American embassies in Brussels to mark the 250th anniversary of the United States. About 20 minutes later, roughly eight Belgian police officers in plain clothes surrounded us and pulled us out of the event. It is unclear whether the police presence that removed us was paid for by the American organisers or by Belgian taxpayers.
```

## GitHub Pages article

Article URL: https://karpathy.github.io/2015/05/21/rnn-effectiveness/

Extraction succeeded: True
Extraction time seconds: 0.165
Extracted title: The Unreasonable Effectiveness of Recurrent Neural Networks

### Output A: Title only

Word count: 7

```text
The Unreasonable Effectiveness of Recurrent Neural Networks
```

### Output B: Title + meta description

Word count: 11

```text
The Unreasonable Effectiveness of Recurrent Neural Networks

(meta description not available)
```

### Output C: Title + first meaningful paragraph

Word count: 171

```text
The Unreasonable Effectiveness of Recurrent Neural Networks

There’s something magical about Recurrent Neural Networks (RNNs). I still remember when I trained my first recurrent network for Image Captioning. Within a few dozen minutes of training my first baby model (with rather arbitrarily-chosen hyperparameters) started to generate very nice looking descriptions of images that were on the edge of making sense. Sometimes the ratio of how simple your model is to the quality of the results you get out of it blows past your expectations, and this was one of those times. What made this result so shocking at the time was that the common wisdom was that RNNs were supposed to be difficult to train (with more experience I’ve in fact reached the opposite conclusion). Fast forward about a year: I’m training RNNs all the time and I’ve witnessed their power and robustness many times, and yet their magical outputs still find ways of amusing me. This post is about sharing some of that magic with you.
```

### Output D: Title + LSA extractive summary

Word count: 49

```text
The Unreasonable Effectiveness of Recurrent Neural Networks

Let $\mathcal{F}$ be a fibered complex. Let $\mathcal{F}$ be a category. \begin{enumerate} \item \hyperref[setain-construction-phantom]{Lemma} \label{lemma-characterize-quasi-finite} Let $\mathcal{F}$ be an abelian quasi-coherent sheaf on $\mathcal{C}$. Let $\mathcal{F}$ be a coherent $\mathcal{O}_X$-module.
```

### Output E: Title + LexRank summary

Word count: 103

```text
The Unreasonable Effectiveness of Recurrent Neural Networks

Written as a class, the RNN’s API consists of a single step function: rnn = RNN() y = rnn.step(x) # x is an input vector, y is the RNN's output vector The RNN class has some internal state that it gets to update every time step is called. At test time, we feed a character into the RNN and get a distribution over what characters are likely to come next. The input in each case is a single file with some text, and we’re training an RNN to predict the next character in the sequence.
```

### Output F: Title + TextRank summary

Word count: 100

```text
The Unreasonable Effectiveness of Recurrent Neural Networks

Written as a class, the RNN’s API consists of a single step function: rnn = RNN() y = rnn.step(x) # x is an input vector, y is the RNN's output vector The RNN class has some internal state that it gets to update every time step is called. Fun with RNNs All 5 example character models below were trained with the code I’m releasing on Github. The input in each case is a single file with some text, and we’re training an RNN to predict the next character in the sequence.
```
