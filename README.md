# AI-Driven Development Test: Banking REST Service

A RESTful banking API built with AI-driven development practices. This service provides core banking functionality including account management, transactions, money transfers, card management, and statement generation.

## Project Requirements

### Core Components:

1. **Service Interface**
   ● Signing up
   ● Authentication
   ● Account Holders
   ● Accounts
   ● Transactions
   ● Money Transfer
   ● Cards
   ● Statements
2. **Database** (using SQLite)
   ● Database implementation
3. **Test Suite** (not a hard requirement as the focus is more on your code)
   ● Comprehensive test coverage for critical functionality
   ● Unit tests for business logic
   ● Integration tests for API endpoints

## Action steps

1. Finalize project scope (MVP vs optional features)
2. Establish technology stack and AI-assisted workflow
3. Define technical architecture and API endpoint contracts
4. Implement database models and schema migrations
5. Implement authentication and account holder flows
6. Implement accounts, transactions, and transfer logic
7. Implement statements and cards (cards optional if time-constrained)
8. Manually test API flows (Swagger/Postman/curl)
9. Add test suite for critical functionality
10. Complete documentation (security, roadmap, AI usage report/log)
11. Final review, cleanup, and submission packaging

## TODO

* [X] TC: Establish tech-stack - prompt to select the tech-stack for the project
* [ ] SC: Source code with core components for service/DB development, config files, test units
* [ ] BP: Test client application for the flow + UI
* [ ] DocAI: Track progress of AI usage - report of tools, prompts, challenges solved with AI, manual interventions
* [ ] DocSecurity: Security considerations document
* [ ] DocRoadmap: Roadmap document for future considerations

## Technology Stack

| Layer            | Technology                                                       | Rationale                                                      |
| ---------------- | ---------------------------------------------------------------- | -------------------------------------------------------------- |
| Framework        | [FastAPI](https://fastapi.tiangolo.com/)                            | Modern, async Python web framework with automatic OpenAPI docs |
| Database         | SQLite +[SQLAlchemy](https://www.sqlalchemy.org/)                   | Lightweight relational DB with a powerful Python ORM           |
| Auth             | JWT (via[python-jose](https://github.com/mpdavis/python-jose))      | Stateless, industry-standard authentication                    |
| Password Hashing | [passlib](https://passlib.readthedocs.io/) + bcrypt                 | Secure credential storage                                      |
| Validation       | [Pydantic v2](https://docs.pydantic.dev/)                           | Runtime type validation built into FastAPI                     |
| Testing          | [pytest](https://pytest.org/) + [httpx](https://www.python-httpx.org/) | Async-compatible test client for API integration tests         |
| Migrations       | [Alembic](https://alembic.sqlalchemy.org/)                          | Schema versioning for SQLite                                   |

## Architecture

![Architecture](assets/architecture.png)
