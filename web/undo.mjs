// Web-side command stack. Commands are opaque { label, before, after }.
// The stack does not know about OCCT. push() drops the redo list and returns
// those commands so the caller can free snapshots. clear() returns every
// command the same way. undo() and redo() return the command to apply.

export function createCommandStack() {
  const past = [];
  const future = [];

  return {
    push(cmd) {
      const dropped = future.splice(0, future.length);
      past.push(cmd);
      return dropped;
    },
    undo() {
      if (!past.length) return null;
      const cmd = past.pop();
      future.push(cmd);
      return cmd;
    },
    redo() {
      if (!future.length) return null;
      const cmd = future.pop();
      past.push(cmd);
      return cmd;
    },
    clear() {
      return past.splice(0, past.length).concat(future.splice(0, future.length));
    },
    depth() {
      return past.length;
    },
    redoDepth() {
      return future.length;
    },
  };
}
