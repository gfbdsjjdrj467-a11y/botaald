#!/bin/sh

#
# Copyright 2015 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -e

APP_NAME="Gradle"
APP_BASE_NAME=$(basename "$0")
APP_HOME=$(cd "$(dirname "$0")" && pwd -P)
APP_PATH="$APP_HOME/gradle/wrapper/gradle-wrapper.jar"
PROP_FILE="$APP_HOME/gradle.properties"
SCRIPT="$0"

while [ -h "$SCRIPT" ]; do
  ls=$(ls -ld "$SCRIPT")
  link=$(expr "$ls" : '.*-> \(.*\)$')
  if expr "$link" : '/.*' > /dev/null; then
    SCRIPT="$link"
  else
    SCRIPT="$APP_HOME/$(cat "$SCRIPT")"
  fi
done

DIR=$(cd "$(dirname "$SCRIPT")" && pwd -P)

exec "$DIR/gradle/wrapper/gradle-wrapper.jar" "$@"
