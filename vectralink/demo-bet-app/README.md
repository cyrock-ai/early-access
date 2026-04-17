# Betting Application Demo

## Overview

This is a demo betting application showcasing a complete sports betting domain model with REST API endpoints. The application automatically generates and manages sports, competitions, events, markets, selections, and odds data.

## Tech Stack

- **Java 21**
- **Spring Boot 3.5.8**
  - Spring Data JPA
  - Spring Web MVC
  - Spring Validation
- **Hibernate 6.6** (JPA provider)
- **MySQL 8.0** (via Testcontainers)
- **Qdrant v1.15.5** - Vector database (via Testcontainers)
- **Debezium 3.3** - Change Data Capture (embedded, no Kafka needed)
- **Testcontainers** (automatic MySQL & Qdrant startup)
- **Springdoc OpenAPI 3** (Swagger UI)
- **Maven** (build tool)

## Features

- 🏆 **Full betting domain model** with cascading persistence
- 🔄 **Automatic data generation** (sports, competitions, events, markets, odds)
- 📊 **REST API** with OpenAPI/Swagger documentation
- 🐳 **Testcontainers integration** - MySQL & Qdrant start automatically (no manual setup needed)
- ⚡ **Scheduled odds updates** (simulated real-time odds changes)
- 🎯 **Transaction management** with optimistic locking
- 🔍 **Real-time vector sync** - Odds changes automatically synchronized to Qdrant vector database
- 🔄 **CDC with Debezium** - Captures MySQL odds table changes in real-time
- 🧠 **AI-ready** - Odds data automatically vectorized for ML/AI applications

## Quick Start

### Prerequisites
- Java 21 or higher
- Maven 3.6+
- Docker (for Testcontainers - MySQL & Qdrant)

### Run the application

```bash
# Clone and navigate to the project
cd demo-bet-app

# Run (dev profile is active by default - starts MySQL & Qdrant via Testcontainers)
mvn spring-boot:run
```

The application starts on **http://localhost:8080**

**Containers started automatically:**
- **MySQL container**: `localhost:3306` (mapped port)
- **Qdrant container**: 
  - HTTP API: `localhost:6333` (mapped port)
  - gRPC API: `localhost:6334` (mapped port)

### Access Swagger UI
Open your browser: **http://localhost:8080/swagger-ui**

## REST API

All REST API endpoints are fully documented in **Swagger UI**: **http://localhost:8080/swagger-ui**

Key endpoints:
- **Sports management**: GET/POST `/sports`
- **Opportunity search**: GET `/api/opportunities/by-odds-range`, `/api/opportunities/by-event`
- **Market management**: POST `/api/opportunities/add-market`

Swagger UI provides interactive documentation with request/response examples and "Try it out" functionality.

| Class | Čeština | English | Deutsch | Example |
| --- | --- | --- | --- | --- |
| `Sport` | Reprezentuje sport (např. fotbal), obsahuje seznam soutěží. | Represents a sport (e.g. football), contains a list of competitions. | Repräsentiert eine Sportart (z. B. Fußball), enthält eine Liste von Wettbewerben. | name: Football, code: FOOT |
| `Competition` | Soutěž / liga v rámci sportu, obsahuje události (events). | A competition/league within a sport, contains events. | Wettbewerb/Liga innerhalb eines Sports, enthält Events. | Premier League (England, 2024/25) |
| `Event` | Konkrétní zápas/událost s časem, statusem, metadaty a trhy. | Specific match/event with start time, status, metadata and markets. | Konkretes Spiel/Ereignis mit Startzeit, Status, Metadaten und Märkten. | Manchester United vs Chelsea (2025-05-10T19:30:00Z, SCHEDULED) |
| `Market` | Trh v rámci události (např. match odds), obsahuje výběry. | Market within an event (e.g. match odds), contains selections. | Markt innerhalb eines Events (z. B. Match Odds), enthält Auswahlmöglichkeiten. | Match Odds (live: false) |
| `Selection` | Jednotlivá volba na trhu (např. Home, Away) s kurzy. | Individual choice on a market (e.g. Home, Away) with odds. | Einzelne Auswahl im Markt (z. B. Home, Away) mit Quoten. | Home (ref: HOME), odds: 1.85 |
| `Odds` | Aktuální kurz, čas aktualizace, poskytovatel a historie bodů. | Current odds, update timestamp, provider and history points. | Aktuelle Quote, Aktualisierungszeit, Anbieter und Verlauf. | 1.85 @ providerA, updated: 2025-05-01T12:00:00Z |
| `OddsPoint` | Historický záznam kurzu v konkrétním čase. | Historical odds record at a specific timestamp. | Historischer Quoteneintrag zu einem bestimmten Zeitpunkt. | 2025-05-01T12:00Z–2025-05-01T13:00Z: 1.90 |
| `BetSlip` | Sázkový lístek s více sázkami, celkovým stake a potenciální výhrou. | Betslip with multiple bets, total stake and potential payout. | Wettschein mit mehreren Wetten, Gesamteinsatz und möglicher Auszahlung. | bets: 2, stake: 10.00 EUR, potential payout: 42.50 EUR |
| `Bet` | Jedna vsazená položka: odkazy na event/market/selection, stake a stav. | Single placed bet: references to event/market/selection, stake and status. | Einzelne platzierte Wette: Verweise auf Event/Market/Selection, Einsatz und Status. | selectionId: <uuid>, stake: 10.00, placedOdds: 4.25, status: PENDING |
| `User` | Uživatelský účet s identitou, zůstatkem a měnou. | User account with identity, balance and currency. | Benutzerkonto mit Identität, Kontostand und Währung. | username: alice, currency: EUR, balance: 100.00 |
| `Transaction` | Finanční transakce uživatele (vklad, výběr, stake, výhra) s referencí. | User financial transaction (deposit, withdrawal, stake, win) with reference. | Finanztransaktion des Nutzers (Einzahlung, Auszahlung, Einsatz, Gewinn) mit Referenz. | type: DEPOSIT, amount: 50.00 EUR, ref: TX-123 |
| `EventStatus` | Enum stavů události (SCHEDULED, LIVE, FINISHED, ...). | Enum of event statuses (SCHEDULED, LIVE, FINISHED, ...). | Enum der Event-Status (SCHEDULED, LIVE, FINISHED, ...). | e.g., LIVE |
| `MarketType` | Enum typů trhu (MATCH_ODDS, TOTALS, HANDICAP, ...). | Enum of market types (MATCH_ODDS, TOTALS, HANDICAP, ...). | Enum der Markt-Typen (MATCH_ODDS, TOTALS, HANDICAP, ...). | e.g., MATCH_ODDS |
| `BetStatus` | Enum stavů sázky (PENDING, ACCEPTED, SETTLED_WON, ...). | Enum of bet statuses (PENDING, ACCEPTED, SETTLED_WON, ...). | Enum der Wett-Status (PENDING, ACCEPTED, SETTLED_WON, ...). | e.g., PENDING |

## Domain Model Architecture

The application implements a complete hierarchical betting domain model:

```text
+------------------+
| Sport            |
| - id, name, code |
+------------------+
         |
         | @OneToMany (CascadeType.ALL)
         v
+---------------------------+
| Competition               |
| - id, name, country       |
| - season                  |
+---------------------------+
         |
         | @OneToMany (CascadeType.ALL)
         v
+---------------------------------------+
| Event                                 |
| - id, name, startTime, status         |
| - metadata (Map<String,String>)       |
+---------------------------------------+
         |
         | @OneToMany (CascadeType.ALL)
         v
+-------------------------------+
| Market                        |
| - id, type, name, live        |
+-------------------------------+
         |
         | @OneToMany (CascadeType.ALL)
         v
+-------------------------------+
| Selection                     |
| - id, name, reference         |
+-------------------------------+
         |
         | @OneToOne (CascadeType.ALL)
         v
+---------------------+    +------------------+
| Odds                |    | OddsPoint        |
| - value, updated    |<---| - value          |
| - provider          |    | - timestamp      |
+---------------------+    +------------------+
        @OneToMany (CascadeType.ALL)

Betting & User Domain (separate aggregates):
+---------+    +--------+     +----------------------------+
| BetSlip |    | Bet    |     | References                 |
| - total |<-->| - stake|---->| event/market/selection ids |
| - status|    | - odds |     +----------------------------+
+---------+    +--------+

+-------------------------+    +-------------------------+
| User                    |    | Transaction             |
| - username, email       |<-->| - type, amount          |
| - balance, currency     |    | - reference             |
+-------------------------+    +-------------------------+
```

### Key Enums:
- **EventStatus**: SCHEDULED, LIVE, FINISHED, CANCELLED, POSTPONED
- **MarketType**: MATCH_ODDS, TOTALS, HANDICAP, CORRECT_SCORE, FIRST_GOAL, OTHER
- **BetStatus**: PENDING, ACCEPTED, SETTLED_WON, SETTLED_LOST, CANCELLED, REFUNDED

### Data Cascade Strategy
- **Sport → Competition → Event → Market → Selection → Odds** uses `CascadeType.ALL` + `orphanRemoval=true`
- Saving a `Sport` automatically persists the entire hierarchy
- Deleting a `Sport` removes all related entities

---

## 🔍 Vectralink Integration - Real-time Odds Synchronization

### Overview

The application integrates **Vectralink** - a CDC (Change Data Capture) to vector store synchronization framework. It automatically:
1. Captures changes to the **`odds`** table using **Debezium**
2. Vectorizes odds data (value, provider)
3. Stores vectors in **Qdrant** vector database
4. Enables real-time synchronization of odds changes

### Architecture

```
MySQL (odds table)
    ↓ CDC (Debezium)
VectorStoreUpdater
    ↓ Vectorization (2D: value, provider)
Qdrant Vector Store (collection: "odds")
```

### Vectorization Strategy

Each odds record is converted to a **2-dimensional vector**:
- **Dimension 1**: Normalized odds value (0-1, max 100)
- **Dimension 2**: Provider hash (0-1, based on provider name)

Similarity is calculated using **cosine distance** in Qdrant.

### How it Works

#### When Sports are Generated
```
POST /sports/add?count=5
    ↓
Creates: Sport → Competition → Event → Market → Selection → Odds
    ↓
Debezium captures INSERT on odds table
    ↓
Vectorization: [normalized_value, provider_hash]
    ↓
Stored in Qdrant collection "odds"
```

#### When Odds are Updated (OddsScheduler)
```
OddsScheduler runs every 30s
    ↓
Updates Odds.value in MySQL
    ↓
Debezium captures UPDATE on odds table
    ↓
Re-vectorization with new value
    ↓
Updated in Qdrant collection "odds"
```

### Configuration

Vectralink is configured in `VectralinkConfig.java`:
- **Vectorizer**: Converts odds data to 2D vector [value, provider]
- **QdrantVectorStore**: Manages "odds" collection in Qdrant
- **DebeziumConnector**: Monitors MySQL `odds` table using **Debezium Embedded Engine** (file-based, **no Kafka required**)
- **Snapshot mode**: `initial` - captures existing odds on first start, then monitors changes

**Note:** This implementation uses Debezium Embedded Engine with file-based offset storage, eliminating the need for Apache Kafka or Kafka Connect infrastructure.

### Benefits

- ⚡ **Real-time sync** - Odds changes automatically reflected in vector store
- 🎯 **AI-ready** - Odds vectors enable ML/AI analysis and predictions
- 🚀 **Fast vectorization** - Millisecond-level synchronization
- 📊 **Historical tracking** - All odds changes are captured and vectorized

### 🔍 Opportunity Search API

The application provides a REST API for searching betting opportunities using vector search:

#### Endpoints

**1. Search by Odds Range**
```bash
GET /api/opportunities/by-odds-range?minOdds={min}&maxOdds={max}
```
Returns all betting opportunities (Sport → Competition → Event → Market → Selection → Odds) where odds value is within the specified range.

**Example:**
```bash
curl -X GET "http://localhost:8080/api/opportunities/by-odds-range?minOdds=2.0&maxOdds=5.0"
```

**Response:** List of `OpportunityDto` with complete hierarchy including sport, competition, event, market, selection, and odds information.

**2. Search by Event and Odds Range**
```bash
GET /api/opportunities/by-event?eventId={id}&minOdds={min}&maxOdds={max}
```
Returns betting opportunities for a specific event within the odds range.

**Example:**
```bash
curl -X GET "http://localhost:8080/api/opportunities/by-event?eventId=1&minOdds=1.5&maxOdds=10.0"
```

#### Implementation Details

- **Vector Search**: Uses Qdrant vector store to find odds within range using cosine similarity
- **Post-filtering**: Results are filtered by exact odds range after vector search
- **Eager Loading**: All entity relationships are loaded in a single query to avoid N+1 problems
- **Performance**: Searches millions of odds records in milliseconds

#### How it Works

1. **Query Vector Creation**: Creates a vector from the center of the odds range
2. **Similarity Search**: Qdrant finds 1000 most similar vectors
3. **Range Filtering**: Filters results to exact min/max odds range
4. **Data Retrieval**: Fetches complete entities with all relationships from database
5. **DTO Mapping**: Maps entities to flat DTOs with complete hierarchy

### 🎯 Add Custom Betting Markets

The application provides an endpoint for adding new betting markets to existing events:

**Endpoint:** `POST /api/opportunities/add-market`

**Supported Market Types:**
- **MATCH_ODDS** - Match winner (1X2, Home/Draw/Away)
- **TOTALS** - Over/Under goals (e.g., Over/Under 2.5)
- **HANDICAP** - Handicap betting (Asian/European handicap)
- **CORRECT_SCORE** - Exact score prediction (1-0, 2-1, etc.)
- **FIRST_GOAL** - First goal scorer, time of first goal
- **OTHER** - Other markets (Both teams to score, Clean sheet, etc.)

Request format, examples, and response schemas are available in **Swagger UI**.

#### Examples of Custom Markets

Various market types are supported including:
- **First Goal Scorer** - Player predictions
- **Over/Under Goals** - Total goals betting
- **Both Teams to Score** - Yes/No markets
- **Correct Score** - Exact score predictions

Full examples and request formats are available in **Swagger UI**.

#### CDC Synchronization

When you add a new market with odds:
1. Market, selections, and odds are saved to MySQL (cascading persistence)
2. Debezium CDC captures the INSERT on the `odds` table
3. Odds are automatically vectorized and stored in Qdrant
4. New odds become immediately searchable via vector search API

This allows you to:
- Create custom betting markets dynamically
- Add multiple selections with different odds
- Automatically sync new odds to vector store
- Search for new opportunities instantly using vector search

#### Testing

The application includes comprehensive integration tests using Testcontainers (MySQL + Qdrant):

**OpportunityServiceVectorSearchIT** - Tests vector search functionality:
- Uses `MarketService.addMarketToEvent()` to create specific test data
- Tests precise odds range filtering (e.g., "find odds between 2.0 and 5.0")
- Validates event-specific searches
- Tests multiple market types (FIRST_GOAL, TOTALS, CORRECT_SCORE)
- Verifies complete hierarchy data in responses
- All tests use known odds values for deterministic validation

**MarketServiceIT** - Tests market creation:
- First Goal Scorer markets
- Over/Under (Totals) markets
- Both Teams to Score markets
- Correct Score markets
- Validation of invalid inputs

Example test showing precision of vector search:
```java
// Create market with known odds
marketService.addMarketToEvent(new AddMarketRequest(
    eventId,
    "First Goal Scorer",
    "FIRST_GOAL",
    false,
    List.of(
        new SelectionRequest("Ronaldo", "PLAYER_7", BigDecimal.valueOf(2.50), "Bet365"),
        new SelectionRequest("Messi", "PLAYER_10", BigDecimal.valueOf(3.75), "Bet365"),
        new SelectionRequest("Benzema", "PLAYER_9", BigDecimal.valueOf(4.20), "Bet365")
    )
));

// Search and verify exact odds
List<OpportunityDto> opportunities = opportunityService.findByOddsRange(2.0, 5.0);
assertThat(opportunities)
    .extracting(OpportunityDto::getSelectionName)
    .contains("Ronaldo", "Messi", "Benzema");
```

---

## Running the application with MySQL (Testcontainers)

This application automatically starts MySQL and Qdrant using Testcontainers when you run it (no manual setup needed).

Requirements:
- Docker (Docker Desktop or another Docker daemon) must be running on your machine.
- JDK 21 or higher and Maven must be installed.

Run the application:

```bash
# Start the app (Testcontainers will start MySQL & Qdrant automatically)
mvn spring-boot:run
```

Or after building:

```bash
mvn clean package -DskipTests

java -jar target/demo-bet-app-1.0.0-SNAPSHOT.jar
```

How it works:
- `TestcontainersMySQLConfig` starts a `MySQLContainer` at JVM startup
- `TestcontainersQdrantConfig` starts a `QdrantContainer` at JVM startup
- Hibernate is configured with `spring.jpa.hibernate.ddl-auto=update` so the schema will be created/updated automatically
- Debezium CDC connector starts automatically and monitors the `odds` table

Using an external MySQL instance:
- To use your own database, set the datasource properties in `src/main/resources/application.properties` or pass them as environment variables:

```
spring.datasource.url=jdbc:mysql://YOUR_HOST:3306/yourdb
spring.datasource.username=youruser
spring.datasource.password=yourpass
spring.jpa.hibernate.ddl-auto=update
```

Note:
- Testcontainers is convenient for development and demos. For production, use managed MySQL and Qdrant instances and manage schema migrations with Flyway or Liquibase.

---

## 📋 TODO - Planned Features

The following features are planned for future development and not ready yet:

### 🔐 User Management
- [ ] User registration and authentication
- [ ] User profile management
- [ ] Balance management (deposits, withdrawals)
- [ ] Transaction history
- [ ] User roles and permissions

### 🎯 Betting Functionality
- [ ] Place bets endpoint (create Bet and BetSlip)
- [ ] Bet validation (odds availability, balance check)
- [ ] Bet settlement logic (calculate payouts)
- [ ] Bet history and tracking
- [ ] Multi-bet support (accumulator/parlay)
- [ ] Cash-out functionality

### 📊 Advanced Features
- [ ] Live betting support (real-time odds updates during events)
- [ ] Bet recommendations based on vector similarity
- [ ] Event result integration

### 🔍 Vector Search Enhancement
- [ ] Similarity search API for odds patterns
- [ ] Historical odds analysis
- [ ] Predictive odds modeling
- [ ] Anomaly detection in odds movements

### 🏗️ Infrastructure
- [ ] Production profile configuration
- [ ] Monitoring and observability (Prometheus, Grafana)

---


