# Stochastic Methods in Quant Trading: Using Randomness to Model Systems

*Exploring the use cases of Geometric Brownian Motion in Systematic Trading*

**Author:** William Nelson
**Created:** 15 July 2025
**Last Updated:** 17 July 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Brownian and Geometric Brownian Motion](#brownian-and-geometric-brownian-motion)
3. [Ornstein-Uhlenbeck Process](#ornstein-uhlenbeck-process)
4. [Monte Carlo Methods](#monte-carlo-methods)
5. [Hidden Markov Models](#hidden-markov-models)
6. [Kalman and Particle Filters](#kalman-and-particle-filters)
7. [Stochastic Vol Models](#stochastic-vol-models)
8. [Summary](#summary)

---

## Introduction

Markets are inherently uncertain. Prices fluctuate not only due to economic fundamentals, but also because of unpredictable investor behaviour, external shocks, and structural noise.

To model such environments, quants and engineers often turn to stochastic processes. These are mathematical frameworks that treat variables as probabilistic rather than deterministic.

Stochastic models don't aim to perfectly predict future prices. Rather they quantify uncertainty, vol, and likelihoods, enabling traders to build systems that can operate under uncertainty in a consistent, probabilistic way.

In systems trading stochastic models are used to simulate prices, estimate hidden market states, detect patterns obscured by noise, and assess risk and return of systems.

Stochastic models are used for:

- Price path simulation
- Risk estimation
- Regime detection
- Signal extraction
- Vol modelling

The sections that follow will walk through the most widely used stochastic methods in systematic trading - from Brownian motion to filtering techniques and vol models. Each method will be analysed through a consistent lens: theory, application, implementation, and limitations.

---

## Brownian Motion and Geometric Brownian Motion: The Building Block for Stochastics in Trading

Stochastics are something that changes over time in a random way.

**Brownian Motion** is the most basic type of stochastic process - a smooth and continuous random walk with no memory.

Brownian motion is the cornerstone of modern stochastic modelling. It is used as a mathematical model with continuous-time randomness.

If you use Brownian motion in your models, you assume complete random direction, and that the next price move is independent of the last, but the price movement is smooth.

If you use **Geometric Brownian Motion** in your models, the price will go up or down on average, but still with randomness; you also assume returns follow a bell curve. Essentially GBM is about overall price direction but with noise along the way.

Brownian motion is all about price evolution, and the most widely used variant, Geometric Brownian Motion, models asset prices as a continuous-time stochastic process with drift and vol. GBM underpins Black-Scholes and is usually the starting point for simulating asset price paths.

**Where to use GBM in trading:**

GBM is used for option pricing, Monte Carlo sims, vol scaling, and portfolio allocation. You'll find it in tools like Kelly sizing, Monte Carlo sims, and more, but GBM alone is hardly used in trading — it's the backbone of stochastic models.

**Why GBM over BM in systems:**

GBM is more realistic for asset price paths, can simulate compounding returns, and has a long-term trend feature built into the randomness of the model. This makes GBM more realistic than BM for systems.

---

## Ornstein-Uhlenbeck Process: The Mean-Reversion 'Full Package'

Not all assets drift endlessly like stocks. Interest rates, vol, and spreads tend to mean revert.

The **Ornstein-Uhlenbeck (OU) process** is one of the most common ways to model this behaviour. It describes a system where random movement still occurs (uses BM), but there's a pull back toward a long-term average — perfect for mean reversions.

**Where to use OU in trading:**

Any kind of mean-reverting model, commonly a Z-spread reversion — for example, stocks like Pepsi and Coke.

You could create a static rule-based Z-spread reversion system (think SD thresholds for entry + exit), or use OU which is more of an actual 'model' — it filters noise way better, integrates dynamic sizing, entry confidence, and deals with vol regimes well.

For mean reversion systems, OU is the full package.

---

## Monte Carlo Methods: The Forecasting Tool

Monte Carlo methods are all about simulating uncertainty.

Rather than solving equations exactly, you iterate lots of random simulations to see what outcomes are possible — and then analyse those outcomes.

**Uses in quant trading:**

- Simulating price paths
- Forecasting system (portfolio) value
- Estimating risk measures (e.g. VaR)
- Pricing complex derivatives

Quite literally, Monte Carlo is: *"If we don't know the future, let's simulate thousands of possible scenarios — and make decisions based on their patterns."*

Monte Carlo isn't a model — it's a numerical method that uses random sampling to estimate behaviour in a system. To model the randomness of different price paths, Monte Carlo typically runs off GBM.

Monte Carlo is essential for risk, forecasting, and pricing.

---

## Hidden Markov Models: Vol Regimes

Markets often enter different vol regimes. **HMMs** are designed to capture regime-switching behaviour, where the market is in one of several possible 'states' — but you can't observe those states directly.

What HMMs assume is that there's an underlying state, and what you observe is generated based on that hidden state.

HMMs estimate the probabilities of being in each regime and how likely transitions are from one to another — making it a powerful tool for detecting structural changes in the market.

**Where to use HMMs in trading:**

- Regime detection (use this to switch or adapt systems)
- Vol modelling
- Signal filtering (different regimes should only allow certain signals)
- Dynamic allocation (shift risk exposure based on regime)

HMMs are used as meta-models in systems — they don't generate signals but they're there to alter the behaviour of other functions, which helps with regime adaptability.

---

## Kalman and Particle Filters: Dynamic Noise Filters

In markets, most of the noise you see is just a reflection of a deeper, hidden signal or trend or factor that you're trying to track.

**Kalman Filters** and their nonlinear cousin, **Particle Filters**, are methods for estimating hidden variables in real time, based on noisy observations and assumptions about how these variables evolve.

They're especially useful when:

- You believe there's an underlying signal
- That signal changes over time
- The data is too noisy to observe it directly

They work by using Bayesian Updating to balance confidence in the filter's model of the signal and the noisy data — then over time build an estimate of the true signal.

**Kalman Filter vs Particle Filter:**

| | Kalman Filter | Particle Filter |
|---|---|---|
| **Use for** | Linear data | Nonlinear data |
| **Noise assumption** | Gaussian | Flexible |
| **Speed** | Fast | Computationally expensive |
| **Deployment** | Common in live systems | Rarely live-deployed |

**Where to use Kalman/Particle Filters in trading:**

- Trend estimation (filter short-term noise to estimate the true price trend)
- Estimating hidden vol
- Separating signal from noise in real time

In short, these filters let you isolate signal from noise, in real time, with dynamic adjustment.

---

## Stochastic Vol Models (GARCH, Heston, SABR): Essentials for Vol Systems

In most basic models (especially ones using GBM), vol is assumed constant. But in real markets this is not true: vol clusters, changes over time, and is often mean-reverting but not predictable in a straight line.

Stochastic vol models explicitly model vol as a random process:

> *"Vol itself is volatile — and we can model that uncertainty with its own set of rules."*

This gives systems more realistic inputs for pricing, risk, and dynamic position sizing.

**The three key models:**

| Model | Best Used For | Role in System |
|---|---|---|
| **GARCH** | Forecasting next-period RV from past returns | Signal logic, risk infrastructure |
| **Heston** | Equity and index option pricing; skew plays | Signal logic + risk (vol traders) |
| **SABR** | FX and rates option pricing | Current vol surface for dealing |

**Model details:**

- **GARCH** — forecasts future vol from past returns. Sits in strategy infrastructure (signal logic, risk).
- **Heston** — produces a full vol surface based on stochastic modelling. Used for equity/index skew. Vol surface is cached rather than recalculated on every run (computationally efficient). Valid as a signal generator for vol traders.
- **SABR** — produces the current vol surface directly. More useful for dealing in rates and FX. Cannot model the downside-heavy structure of equity/index options (Heston handles that better).

All three models derive their forecasts from the key assumption of stochastic (specifically BM) vol, which is structured and statistically realistic.

---

## Summary

| Method | Purpose |
|---|---|
| **Brownian Motion** | The randomness foundation |
| **Geometric Brownian Motion** | Exponential price evolution under randomness |
| **Ornstein-Uhlenbeck Process** | Mean-reverting noise model for spread-based systems |
| **Monte Carlo Simulation** | Simulate uncertainty by running many random paths |
| **Kalman Filter** | Adaptive noise filter for extracting true signals |
| **GARCH Models** | Time-based volatility forecasting from past returns |
| **Heston Model** | Dynamic vol-price model for realistic option pricing and skew |
| **SABR Model** | Smile-fitting tool for current vol surface in FX and rates |
