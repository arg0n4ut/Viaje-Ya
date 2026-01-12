# Viaje-Ya
Simple web app for organizing group trips.

Development in the practical part of the course "Cloud Computing: Fundamentos e Infraestructuras" at the Universidad de Granada, taught by Claudia Villalonga.

## Development status
- project repository set up
- Python virtual environment set up
- testing approach (TDD with pytest) defined and basic test created
- Makefile created to run tests locally and remotely
- continuous integration with GitHub Actions implemented
- Docker Compose stack defined and container publishing workflow targeting GHCR configured
- deployment to Render (PaaS) with MongoDB Atlas (DBaaS) set up

## Motivation
When organizing a group trip, it can be difficult to keep track of places to visit, activities to do, things to pack, etc.

This project's aim is to create a web application that offers tools to help with various aspects of trip organization.

This way, everyone can easily contribute to the planning and have all the important information accessible in one place.

## Features to be implemented (tentative)
- manage trips and participants ✅
- proposal and voting system for destinations and activities ✅
- map integration for destinations and activities
- packing and todo lists ✅
- bundle important informationa and documents
- expense tracking / splitting 

<!-- Tecnologías base: Python (FastAPI/Flask), MongoDB, Docker, GitHub Actions, PaaS (Render/Fly.io). -->
## Technologies to be used (tentative)
- Python (FastAPI/Flask)
- MongoDB
- Docker
- GitHub Actions
- PaaS (e.g. Render/Fly.io)

### Local MongoDB setup
- Configure MongoDB with `MONGODB_URI` (default `mongodb://localhost:27017`) and `MONGODB_DB` (default `viaje_ya`).
- For quick tests run `docker run --rm -d -p 27017:27017 --name viaje-ya-mongo mongo:7`.
- `pytest` uses `mongomock`, so local Mongo is optional.

### Containerised stack
- **viaje-ya-api**: FastAPI service from the root Dockerfile, listens on port 8000, depends on MongoDB.
- **viaje-ya-worker**: same image, runs `python -m app.worker` for background metrics.
- **viaje-ya-mongo**: official MongoDB 7.0 datastore.
- **viaje-ya-mongo-data**: BusyBox container owning the `mongo-storage` volume.
- `compose.yaml` wires services, sets health checks (curl for API, `db.adminCommand('ping')` for Mongo), and passes configuration via environment variables.

Bring the stack up with `make docker-up`, rebuild with `make docker-build`, and clean down with `make docker-down`.

### Compose smoke test
- `src/tests/test_compose.py` starts the stack (skipped when Docker is unavailable or `SKIP_DOCKER_TESTS=1`) and runs API requests to verify trips and participants.

### Container delivery pipeline
- `.github/workflows/container.yml` builds the Docker image on every push or PR, runs the Compose smoke test, and pushes `ghcr.io/arg0n4ut/viaje-ya-app:latest` using `GITHUB_TOKEN`.
- `compose.yaml` consumes the published image while also supporting local overrides via the `build` section.

### Deploy to Render (PaaS) with MongoDB Atlas (DBaaS)
- automatic deploy from GitHub on pushes to `main`
- deployed on render: https://viaje-ya.onrender.com
- with UI: https://viaje-ya.onrender.com/ui

### Milestone documentation
- [Hito 1: Repositorio de prácticas y definición del proyecto](docs-milestones/H1.md)
according to [Hito 1: instructions](https://github.com/cvillalonga/CC-25-26/blob/main/hitos/1.Repositorio.md)
- [Hito 2: Integración continua](docs-milestones/H2.md) according to [Hito 2: instructions](https://github.com/cvillalonga/CC-25-26/blob/main/hitos/2.CI.md)
- [Hito 3: Diseño de microservicios](docs-milestones/H3.md) according to [Hito 3: instructions](https://github.com/cvillalonga/CC-25-26/blob/main/hitos/3.Microservicios.md)
- [Hito 4: Contenedores y composición](docs-milestones/H4.md) according to [Hito 4: instructions](https://github.com/cvillalonga/CC-25-26/blob/main/hitos/4.Contenedores.md)
- [Hito 5: Despliegue de la aplicación en un IaaS o PaaS](docs-milestones/H5.md) according to [Hito 5: instructions](https://github.com/cvillalonga/CC-25-26/blob/main/hitos/5.Despliegue.md)


### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.