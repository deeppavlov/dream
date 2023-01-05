## 0.8.3

- Change `Tag` and `SelfCloseTag` class property name `content` to `innerHTML`
- fix [#60](https://github.com/stonehank/html-to-md/issues/60)
- fix quote in tag attribute can not be detected correctly
- fix `|` escapes in table
- ADD: `tagListener` to custom some props of tag

    (tagName, props: [TagListenerProps](https://github.com/stonehank/html-to-md/blob/master/README.md#TagListenerProps)): [TagListenerReturnProps](https://github.com/stonehank/html-to-md/blob/master/README.md#TagListenerReturnProps) => TagListenerReturnProps`

## 0.8.0

- add eslint and premitter
- sourcecode use es module
- convert to typescript

### 0.7.0

- add `renderCustomTags` in options

### 0.6.1

- add title in a tag
- add input options in demo page

### 0.6.0

- fix undefined language in pre tag

### 0.5.9

- fix p tag add an extra gap when inside text node.
- update get language function define in pre tag.

### 0.5.8

- fix[#45](https://github.com/stonehank/html-to-md/issues/45)

### 0.5.7

1. fixed: keep format in coding block(#44)
2. reset config before start

### 0.5.4 - 0.5.6

- fix [#43](https://github.com/stonehank/html-to-md/issues/43)

### 0.5.2 - 0.5.3

- fix [#42](https://github.com/stonehank/html-to-md/issues/42)

### 0.5.1

- Support attr:align in table
- Add UMD to support browser [#41](https://github.com/stonehank/html-to-md/pull/41)

## 0.5.0

#### Refactor

- Less space
- Change some default configs
- Add typings for typescript [#34](https://github.com/stonehank/html-to-md/pull/34)

### 0.4.4

- Fixed issue #33, use `\s` instead of `' '` in tags attribute detect.

### 0.4.3

- Speed up parse string

### 0.4.2

- Remove `window`

### 0.4.1

- Remove `throw Error`, add some errors test
- Add empty `table` detect, add test case

### 0.4.0

- Remove the first `\n` in some tags
- Escape some character in some tag, like `<b>* abc</b>`
- Fix render issues when `<br>` in `<li>`
- Fix render issues when have `` ` ``(single or multiple) in `<code>` or `<pre>`
- Ignore extra tags if already have `code` tag inside `pre`

### 0.3.9

- Output some raw unvalid content, like `<` in the tag contents.

#### 0.3.8

- Fix when render as raw HTML, remove all the wrap.

#### 0.3.7

- Fixed some tags inside `th`, `td` will cause wrap.Consider `<td><div>ABC</div></td>`
- Add some tags should render as raw HTML inside a table.Consider `<td><ul><li>1</li></ul></td>`

#### 0.3.6

- Add `aliasTags`.
- Remove console in production.

#### 0.3.5

- Remove console.

#### 0.3.4

- Add 'dl,dd,dt' inside default skipTags.
- Fixed some no used space.

#### 0.3.3

- Add 'html' and 'body' inside default skipTags.
- Add `force` options, it can totally overwrite the customize options object.
- Fix some redundant empty line.

##### 0.3.2

- Fixed bugs that cause text after heading tags will not line feed.

##### 0.3.1

- created `CHANGELOG.md`, support `english` readme
- add options, can set the tags resolve strategy
- add `div` to default value of `options:skipTags`
- skipTags will check if need '\n'

##### 0.3.0

- add support for tag`<input type="checkbox" />`
- fixed the bug when `<code>`language is `markdown`
- fixed the bug when `<p>` nest in `<li>`
- fixed some nest tag render bug
- merge tht common use code
