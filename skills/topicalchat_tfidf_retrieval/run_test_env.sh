#!/bin/bash

# change current directory to executable script directory
cd "$(dirname "$0")"

cd ../..

TEST_RESULT_DIR=venv/tests
for ARGUMENT in "$@"; do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
    test_only) TEST_ONLY=true ;;
    test_dir) TEST_RESULT_DIR=${VALUE} ;;
    *) ;;
    esac
done


docker_compose="docker-compose -f docker-compose.yml -f dev.yml -f cpu.yml -f one_worker.yml"
if [ -z "$TEST_ONLY" ]; then 
    echo "Build and run an env" 
    skills="\
        book_tfidf_retrieval \
        entertainment_tfidf_retrieval \
        fashion_tfidf_retrieval \
        movie_tfidf_retrieval \
        music_tfidf_retrieval \
        politics_tfidf_retrieval \
        science_technology_tfidf_retrieval \
        sport_tfidf_retrieval \
        animals_tfidf_retrieval "

    $docker_compose build $skills
    $docker_compose up -d $skills
    sleep 30
    echo "Wait for the env to wake up" 
fi;

function get_sample {
echo "Get sample from $1"
curl -X POST "http://localhost:$2/respond" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"sentences\": [ \"What do you like?\" ], \"utterances_histories\": [ [] ] }"
echo ""
}

get_sample book_tfidf_retrieval 8039
get_sample entertainment_tfidf_retrieval 8040
get_sample fashion_tfidf_retrieval 8041
get_sample movie_tfidf_retrieval 8042
get_sample music_tfidf_retrieval 8034
get_sample politics_tfidf_retrieval 8043
get_sample science_technology_tfidf_retrieval 8044
get_sample sport_tfidf_retrieval 8045
get_sample animals_tfidf_retrieval 8050

function run_tests {
echo "Run tests for $1"
$docker_compose exec $1 python /src/run_test.py --from_url=http://0.0.0.0:${2}/respond
mkdir -p ${TEST_RESULT_DIR}
docker cp $($docker_compose ps -q $1):/tmp/test_results.json ${TEST_RESULT_DIR}/${1}_test_results.json
echo ""
}

run_tests book_tfidf_retrieval 8039
run_tests entertainment_tfidf_retrieval 8040
run_tests fashion_tfidf_retrieval 8041
run_tests movie_tfidf_retrieval 8042
run_tests music_tfidf_retrieval 8034
run_tests politics_tfidf_retrieval 8043
run_tests science_technology_tfidf_retrieval 8044
run_tests sport_tfidf_retrieval 8045
run_tests animals_tfidf_retrieval 8050