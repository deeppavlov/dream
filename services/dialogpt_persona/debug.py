sents = [
	"1",
	"2",
	"3",
	"4",
	"5",
	"6",
	"7"
]

print(list(reversed([f"<{(i)%2+1}>{item}</{(i)%2+1}>" for i, item in enumerate(reversed(sents[-5:]))])))