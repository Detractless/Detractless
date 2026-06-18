# Project Ideas

## 1. Exercise Tracking Engine

A wide and highly accurate calisthenics + cardio exercise tracking engine powered by computer vision.

### Why This Exists

I've looked for fitness games that work with just a webcam and there really aren't many. The ones that exist are either locked to expensive hardware (Kinect, Ring Fit, VR headsets) or they track a handful of movements poorly. There's no open, accurate engine that can recognize a wide range of real exercises using just a standard computer camera. That gap means fitness gaming as a genre has stayed niche when it doesn't have to be.

I do Greasing the Groove calisthenics daily and track everything in a notebook. I want something that can actually see what I'm doing, count reps accurately, verify form, and eventually serve as the foundation for fitness games that other developers can build on top of. Not a closed product, but an engine. If the tracking is good enough, the games will follow.

### Vision

The goal is an open-source exercise recognition engine that makes webcam-based fitness gaming viable. Accurate pose estimation and rep counting across a large exercise library, exposed through a clean API so game developers don't have to solve the hard computer vision problems themselves. Get the engine right and the ecosystem can grow around it.

### Exercise Library

<details>
<summary>Horizontal Push</summary>

- Pushups
- Wide Pushups
- Diamond Pushups
- Clapping Pushups
- Archer Pushups
- Pseudo Planche Pushups
- Decline Pushups
- Incline Pushups
- One Arm Pushup
- Dips
- Ring Dips
- Tiger Bend Pushup

</details>

<details>
<summary>Vertical Push</summary>

- Pike Pushups
- Handstand
- Handstand Pushup
- Planche (tuck/straddle/full)
- Wall Walks
- Handstand Walk

</details>

<details>
<summary>Horizontal Pull</summary>

- Inverted Row
- Archer Row

</details>

<details>
<summary>Vertical Pull</summary>

- Pull-ups
- Chin-ups
- Archer Pull-ups
- Typewriter Pull-ups
- L-sit Pull-ups
- One Arm Pull-up
- Negative Pull-ups
- Muscle Up (bar/ring)
- Skin the Cat

</details>

<details>
<summary>Squat/Legs</summary>

- Bodyweight Squats
- Sumo Squats
- Pistol Squats
- Shrimp Squats
- Sissy Squats
- Bulgarian Split Squats
- Box Squats
- Jump Squats
- Nordic Curls
- Glute Bridge
- Calf Raises
- Jumping Lunges

</details>

<details>
<summary>Carry/Grip</summary>

- Dead Hang
- Farmers Carry

</details>

<details>
<summary>Core/Isometric Holds</summary>

- Plank (front/side)
- Reverse Plank
- Hollow Body Hold
- Superman Hold
- L-sit
- Dragon Flag
- Back Lever
- Front Lever
- Human Flag
- Ab Wheel Rollout
- Hanging Leg Raise
- Toes to Bar
- Windshield Wipers
- V-ups
- Frog Stand/Crow Pose
- Elbow Lever

</details>

<details>
<summary>Cardio/Conditioning</summary>

- Burpees
- Mountain Climbers
- Jump Rope
- Box Jumps
- High Knees
- Jumping Jacks
- Bear Crawl
- Crab Walk
- Marching
- Running in Place

</details>

## 2. Read-Aloud Verification Engine

A speech recognition engine that listens as the user reads aloud from a book, PDF, EPUB, or other text source. The engine follows along in real time, tracking accuracy, fluency, and progress through the material.

### Why This Exists

My younger brother has to read before he gets computer time. Right now that means someone has to sit with him and verify he's actually reading, not just flipping pages. This engine would let him read independently while still being held accountable. He reads out loud, the app follows along, and screen time unlocks only after he finishes the assigned section.

### Core Concepts

- Real-time speech-to-text matched against the source text
- Word-by-word progress tracking with accuracy scoring
- Support for multiple text formats (plain text, PDF, EPUB)
- Configurable reading goals (pages, chapters, time spent, accuracy threshold)
- Completion gating (can integrate with Cold Turkey or other blocking tools to unlock access after reading is done)
- Mispronunciation/skip detection so skimming or mumbling doesn't count

### Broader Use Cases

- Parents enforcing reading time before screen time
- Teachers assigning read-aloud homework with built-in verification
- Language learners practicing pronunciation against native text
- Literacy programs tracking reading fluency over time
- Self-improvement for anyone who wants to read more consistently
