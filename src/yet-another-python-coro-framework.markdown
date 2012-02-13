I've been hacking on two of my favorite personal projects recently, [greenhouse][] and [feather][]. They are a python-based [greenlet][]-based non-blocking I/O framework and webserver, respectively.

[Eventlet][] uses greenlets to create coroutines, and [twisted][], [kamaelia][], [cogen][] and a host of others create them with python 2.5+'s generators-as-threads features. So why re-invent the wheel? For one, as Jeff Atwood explains, it's worth it to re-invent the wheel [if you want to know better how wheels work][]. For another, there were ideas that I wanted to try and places I thought I could improve on the architecture of eventlet in particular.

So what follows is a simplified layout of how greenhouse works, with some notes on where it differs from other notable systems and why.

#### Concurrency is hard. Let's go shopping!

The biggest hurdle in server programming today is dealing with very high levels of concurrency. Once upon a time you could start up a pre-set number of processes or threads in a pool, and every connected client would one of those processes or threads until it sent the response out.

A couple of things have come up challenging this approach, however. Between keep-alive (pretty easy to work around), servers doing side-channel HTTP inside request->response cycles (easy to do, tough to scale), and long-polling applications (crazy hard), that model just doesn't meet the needs of today's web. All of those three things cause the duration of a client-server connection to get bigger, and the idea that a whole process or OS thread is dedicated to servicing only one connection at a time becomes ludicrous.

So the I/O in the server can't be blocking, since blocking here means blocking an entire thread and we can't afford to have that weighty a resource sitting around waiting.

The next problem is that writing code around non-blocking sockets is difficult to do and nearly impossible to abstract away. Much of the problem is related to the subroutine-centric nature of python (and most of the other prominent languages in this domain).

In python function calls, the interpreter keeps track of where you are coming from as well as where you are going, every time. It has to, since you will go back there when you return from the new function. What all python code does is call functions inside of functions inside of functions.

In the one-thread-per-connection model, you can receive data on a socket and that thread will simply pause until the data comes in, letting other threads run (letting other connections be served) by that CPU in the interim. It effectively yields control of the CPU until it needs it again.

Unfortunately if we aren't using a separate thread for every connection, then blocking our current thread will also block other unrelated connections. No good. If we run the server with an infinite loop that checks for I/O on all the connections then fires off the appropriate handlers that's good, but we are killed when we try to do any other I/O inside that request->response cycle (the side-channel HTTP) because to get back up to the global loop we have to return from whatever function we are in, and return from the one wrapping that and so on, totally losing our place in the code.

The main approach of [twisted][] for dealing with this situation is that we don't just return all the way up the stack but we also designate a function to call when the new I/O comes back, so we can resume our place (sort of). This is what I mean by "nearly impossible to abstract away" - it radically changes the way that applications in this system have to be written, and it is much harder and, well twisted, than the programming style of the thread-per-connection system.

#### Greenlet to the rescue

The much more elegant solution provided by greenhouse (as well as eventlet and cogen) depends on an extension to the python interpreter known as [greenlet][]. Greenlet provides a type "greenlet" which wraps a function and instead of invoking it directly you call it's `switch` method. This method stores the entire call stack, basically saving our place in the code, and starts the function of the greenlet to which you are switching on a fresh stack.

So instead of having to return all the way up the stack to our infinite loop, we can just run the event loop in a single greenlet and whenever we want to yield control to let someone else run we just switch to the loop's greenlet. It'll switch back here when it determines that we are ready again (like that our I/O has come back).

#### At least, that's what eventlet does

<strike>
Eventlet, and most other systems like it do exactly what I just described. But this means that yielding to the system translates to switching to the loop greenlet and then letting it switch to the correct next place to go. I think this is twice as much switching as we really need to do there.

Eventlet's main loop just figures out which greenlets should be running based on network events and timeouts, then switches to them in order. As they get back the main loop picks up where it left off so it only re-polls sockets and re-bisects the timeout list after every greenlet that it knows should run has already. This is essentially keeping global scheduler state in the stack of that main greenlet - generate a list of who should run, and while that list is non-empty pop one and switch to it.

Greenhouse totally borrows all that logic, except the part about leaving the scheduler state on the stack of a special greenlet. Instead greenhouse stores its scheduler state globally so that when you yield from a greenlet, before having to switch anywhere greenhouse can figure out where it should be switching to and go straight there, cutting out the middleman main loop. The function to yield to the system says check the list of queued-up-and-ready-to-go and if there's something there pop it and switch, otherwise poll sockets and bisect the timeouts until we do have something queued up. No main loop needed.

Well actually, there still does end up being a main loop just because when greenlets are created they have to be given a "parent" greenlet which defaults to the one in which it was created. This parent greenlet is where it automatically switches when the greenlet's function returns. Greenhouse's main loop greenlet is assigned as the parent to all greenlets it creates, but it only gets switched to by greenlets' functions ending, never by cooperative yielding.
</strike>

EDIT: crazy fact about greenlet I discovered after writing this - stack depth does not get cleared until you switch *up to a parent greenlet*. So once we get more than ``max-recursion-depth / in-greenlet-stack-depth`` greenlets in the scheduler at once, we hit a ``RuntimeError: maximum recursion depth exceeded`` error. greenhouse has been [changed accordingly][] (yielding is now acheived by switching up to the main greenlet).

#### Bringing it all together

At the heart of greenhouse is a class called Event. This is an object with basically just 2 operations: wait and trigger ("trigger" is actually "set" followed immediately by "clear", but it's simpler to think in terms of both together as "trigger"). Wait yields the greenlet we are on until the event is triggered by some other greenlet, at which time our waiter gets queued up to go.

Events are important because they form the bridge - with non-blocking I/O tied to Events, which are tied to that no-main-loop scheduler, greenhouse enables the very same programming style as the thread-per-connection.

Here's how it works. All sockets are automatically set to be non-blocking and they get two events as attributes: "readable" and "writable". When a greenlet tries to receive data from a socket, we try and receive data from the underlying OS socket. If nothing is available yet, the operating system raises and exception that effectively says "you told that socket to be non-blocking, but then you went and did something that would block". Greenhouse interprets that as "nothing here yet" and calls wait on the "readable" event, blocking the greenlet. This is still the greenlet that had tried to receive data; no data is there yet, so that greenlet will get blocked until the I/O comes back just like a thread with blocking I/O.

Whenever the scheduler state runs out of greenlets it knows to be immediately runnable it polls all the sockets that are currently waiting for I/O. Those which can now receive data get their readable event triggered and those which were waiting to be able to send get their writable event triggered.

#### So write your server like it's 1999

I said that this allows you to program in the same style as the one-thread-per-connection system, but even that doesn't quite do this justice.

Threads are scheduled "pre-emptively", meaning they switch without warning. This combines terribly with a feature of threads, shared memory. A simple read-modify-write operation on shared memory can get interrupted somewhere between the read and write, the OS switches to a thread that also changes that memory, and when we eventually get back to the first thread we blow away that other thread's changes. So we have to wrap those read-modify-write sections with locks, which prevents some threads from being able to run and which has overhead of its own, as well as major pitfalls when we forget.

Greenlets, on the other hand, only switch when they are told. This means that you can do all the read-modify-write operations you want and as long as you aren't explicitly yielding or calling socket methods between, you're totally safe. All the beautiful shared memory of threads with none of the obnoxious locking. In case you do need to protect a critical section which includes socket methods, greenhouse provides work-alikes for all of the synchronization classes found in the standard library's threading module (and also a Queue.Queue work-alike).

[greenhouse]: http://github.com/teepark/greenhouse
[feather]: http://github.com/teepark/feather
[greenlet]: http://pypi.python.org/pypi/greenlet
[eventlet]: http://eventlet.net/
[twisted]: http://twistedmatrix.com/
[cogen]: http://code.google.com/p/cogen/
[kamaelia]: http://www.kamaelia.org/
[if you want to know better how wheels work]: http://www.codinghorror.com/blog/archives/001145.html
[changed accordingly]: http://github.com/teepark/greenhouse/commit/92dac2df2d25632160eb16b9e6f155d3544fad12
