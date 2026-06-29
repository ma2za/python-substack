# Heading level 1

## Heading level 2

### Heading level 3

#### Heading level 4

##### Heading level 5

###### Heading level 6

A paragraph with **bold**, *italic*, ***bold italic***, `inline code`, ~~strikethrough~~, and a [link](https://example.com).

A sentence with a numeric footnote[^1] and a named footnote[^note], plus a repeat of the first.[^1]

- Bullet one
- Bullet two with **bold**

1. Ordered one
2. Ordered two

> A blockquote across
> two wrapped lines.

> First quote paragraph.
>
> Second quote paragraph.

```python
# fenced code: footnote-like text must stay literal
x = "[^1]: not a footnote"
print("reference [^1] stays text")
```

```
plain code block without a language
```

---

![A captioned image](https://example.com/image.png)

[![Linked image alt](https://example.com/thumb.png)](https://example.com/target)

`inline code with [^1] inside stays literal`

[^1]: The first footnote, with a [link](https://example.com).
[^note]: A named footnote whose definition spans
    a continuation line in the same paragraph.

    And a second paragraph after a blank line.
[^unused]: This definition is never referenced and should be dropped.
