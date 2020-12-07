Author: [Le The Anh](https://github.com/theanhle)

Example:
```shell script
$ curl -H "Content-Type: application/json" -XPOST -d '{"sentences": ["hey how are you"]}' http://0.0.0.0:3008/sentseg
$ [{"punct_sent":"hey. how are you?","segments":["hey.","how are you?"]}]
```
