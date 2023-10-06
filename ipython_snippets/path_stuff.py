from mock_cli.path import ActualPath  # noqa: F401

# Run in ipython with:
# ipython ./ipython_snippets/path_stuff.py -i

parent = "./tmp"
base = "item-editing-todo.md"

print("you may now do:")
print("path = ActualPath(parent, base, False)")
