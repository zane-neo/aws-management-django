#!/bin/bash

kill -9 `lsof -i:9200 | awk '{print $2}'`