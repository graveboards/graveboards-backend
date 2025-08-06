# Graveboards

## Overview
Graveboards aims to simplify the process of giving leaderboards for osu!beatmaps and track scores without the need for any private servers. We believe the current gameplay experience being limited by the ranked section is not enough and the graveyard already has tons of content for the community to enjoy. To do so, we aim to bring a fresh and easy experience for players and mappers to enjoy osu! even more. 

## Problem Statement
Have you ever wanted to see your score saved on a cool graveyard map that you like? Do you wish that getting a leaderboard was simpler compared to trying and rank your map? Do you ever feel like you can't find the maps that you want to play because the website doesn't let you search for them properly? How about being able to preview a map before trying it out? Graveboards aims to try and solve many inconveniences that players and mappers have with the current state of the game while adding a lot of cool features. 

## Project Goals and Objectives
- **Goals:**
  - Adding leaderboards in graveyarded mapsets.
  - Making it simple for players to save their scores and getting them displayed in a leaderboard and profile.
  - Adding curation features for players and mappers.
  - Creating a brand new web experience where finding maps that you want is easier than ever.

## Project Scope
- **Features:**
  - Create a website called Graveboards, where we show beatmap pages and profile pages and display scores and leaderboards, while also creating a new homepage alternative to osu! website.
  - Create filters in our own database so that finding maps becomes easier for everyone.
  - Create new star rating and pp system.
  - Create social media features such as playlists, likes, favorites, etc.
  - Create map previews so people will see and check the map before downloading it.
  - Create an algorithm for beatmaps recommendations.

- **Limitations:**
  - We don't aim to replace bancho or the main branch of osu! like a private server. We aim to expand the current possibilities that bancho allow us to do.

## Technical Overview
- **Technology Stack:** Javascript, Angular Material, Python, Connexion.
- **Architecture:**

![](http://a.pianosuki.com/u/Graveboards_v1-1.drawio.png)

## Collaboration Plan
- **Roles and Responsibilities:**
  - Back-end devs: Responsible for managing the APIs and out database as well as developing future features such as the algorithms.
  - Front-end devs: Responsible for creating and maitanence of the graveboards website and possible future front end applications.
  - Designers: Responsible for creating visual concepts aimed to improve the UX of the project.
  - Testers: Players and mappers willing to spend the time activelly using the project and giving the team detailed feedback on what can be improved from their user experience. 

- **Contribution Guidelines:** [How to contribute]
  - Open Source: We're open for anyone to join and become a Contributor as long as they're willing to spend the time to get up to date with the entire scope of the project and the veteran contributors.

- **Communication Channels:** [Tools for communication]
  - We're using Visual Studio Code plugin for live coding collaboration for both back end and front end. We're also using discord as the main vehicle for communication.

## Timeline and Milestones
- **Phases:**
  - Phase 1: Modding Queue website. Launch graveboards.net as a modding queue website where we get the first users to Interact with our systems.
  - Phase 2: Launch beatmap pages with leaderboards. At this point, we have all the database ready to receive scores and track beatmap versions.
  - Phase 3: Launch profile pages with all relevant stats and features. At this point, we want all the human curation systems to be done and ready for use.
  - Phase 4: Launch complete filter system. At this point, we want our database to have a lot of data and we have all the requirements to filter them with our goals.
  - Phase 5: Launch brand new homepage. At this point we want to have our algorithms trained and ready to show on front page recommended mapsets.

## Marketing and Outreach
- **Community Engagement:** We plan to use BN modding queues as a way to engage with the mapper side of the Community in our project. As soon as the score tracking and leaderboard displays are ready, we plan to engage with players to test our systems.
- **User Feedback:** All feedback should be directed in our discord server to keep improving the project.

## Funding and Resources
- **Funding Needs:** For now we're doing this as a passion project as well as a potential portfolio project showcase as well.
- **Resource Needs:** foss contributed with the domain purchase, but we would be grateful to have contributions on its renewall.

## Conclusion
Thank you for getting this far. If you liked the project and you believe in its vision, make sure to join us!

# Graveboards Backend

Frontend: https://github.com/FlavioAngnes/graveboards-frontend

## Installation

### Prerequisites

- Python 3.13+

### Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/pianosuki/graveboards.git
    cd graveboards
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv  # On Windows use: py -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create the `.env` file:
    ```
    DEBUG=true
    DISABLE_SECURITY=false
    BASE_URL=<frontend-base-url>  # http://localhost:3000
    JWT_SECRET_KEY=<private-encryption-key>
    JWT_ALGORITHM=<symmetric-algorithm>  # HS256
    ADMIN_USER_IDS=<comma-delimmed-osu-user-ids>  # 2,124493,873961 ...
    
    OSU_CLIENT_ID=<osu-oauth-client-id>
    OSU_CLIENT_SECRET=<osu-oauth-client-secret>
    
    POSTGRESQL_HOST=<db-host>  # localhost
    POSTGRESQL_PORT=<db-port>  # 5432
    POSTGRESQL_USERNAME=<db-username>  # postgres
    POSTGRESQL_PASSWORD=<db-password>
    POSTGRESQL_DATABASE=<db-dbname>
    
    REDIS_HOST=<redis-host>  # localhost
    REDIS_PORT=<redis-port>  # 6379
    REDIS_USERNAME=<redis-acl-username>
    REDIS_PASSWORD=<redis-acl-password>
    REDIS_DB=<redis-db-number>  # 0
    ```

5. Run the application:
    ```bash
    # Development mode:
     python main.py  # On Windows use: py main.py
    ```

## Documentation

The API spec can be viewed locally at: http://localhost:8000/api/v1/ui

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
