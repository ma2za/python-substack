# Heading level 1

## Heading level 2

### Heading level 3

#### Heading level 4

##### Heading level 5

###### Heading level 6

A paragraph with **bold**, *italic*, ***bold italic***, `inline code`, ~~strikethrough~~, and a [link](https://example.com).

A sentence with a numeric footnote[^1] and a named footnote[^note], plus a repeat of the first.[^1]

A footnote whose definition is a list.[^listnote]

- Bullet one
- Bullet two with **bold**

1. Ordered one
2. Ordered two

- Bulleted list with a nested bulleted list:
  - inner bullet a
  - inner bullet b
- Bulleted list with a nested numbered list:
  1. inner number a
  2. inner number b

1. Numbered list with a nested bulleted list:
   - inner bullet a
   - inner bullet b
2. Numbered list with a nested numbered list:
   1. inner number a
   2. inner number b

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

| **Header A** | Header B                    |
|:-------------|:----------------------------|
| Cell 1       | [link](https://example.com) |
| Cell 2       | *italic*                    |

A paragraph with inline math $E=mc^2$ in it.

$$
E=mc^2
$$

![A captioned image](https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png)

[![Linked image alt](https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png)](https://example.com/target)

![Captioned with title](https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png "Caption text from markdown title")

![A locally uploaded image](local_image.png)

`inline code with [^1] inside stays literal`

## Heading with **bold**, *italic*, and a [link](https://example.com)

An autolink to <https://example.com> becomes a link.

[^1]: The first footnote, with a [link](https://example.com).
[^note]: A named footnote whose definition spans
    a continuation line in the same paragraph.

    And a second paragraph after a blank line.
[^unused]: This definition is never referenced and should be dropped.
[^listnote]: - list item one
    - list item two
