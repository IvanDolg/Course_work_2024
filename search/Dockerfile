FROM openjdk:17-alpine
RUN apk add --no-cache fontconfig ttf-dejavu

ARG SPRING_PROFILES_ACTIVE
ENV SPRING_PROFILES_ACTIVE=$SPRING_PROFILES_ACTIVE

ENV KRAINET_ELASTIC_HOST=belrw-elastic
ENV KRAINET_ELASTIC_PORT=9200

WORKDIR /app

COPY target/search-0.0.1-SNAPSHOT.jar search.jar

CMD ["java", "-jar", "search.jar"]