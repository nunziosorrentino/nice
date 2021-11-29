# builtins
import asyncio
import asyncio.subprocess as aiosubprocess
import random
from functools import partial, wraps
import aiohttp
import inspect
import os
import re
import sys
import warnings
import _pyio
from collections import (namedtuple, deque, defaultdict,
                         MutableSequence, OrderedDict)
from operator import itemgetter
from subprocess import (Popen, PIPE)
from typing import List, Sequence
import logging

import time
from contextlib import contextmanager

# pip
try:
    # MUST BE IMPORTED BEFORE BOKEH
    import tornado
    from tornado.platform.asyncio import AsyncIOMainLoop

    AsyncIOMainLoop().install()
    # MUST BE IMPORTED BEFORE BOKEH
except RuntimeError:
    warnings.warn('Could not swap out tornado AIO-loop. Bokeh will not '
                  'be able to run on the main loop')

from bokeh.models import (ColumnDataSource, Range1d, FactorRange, HoverTool,
                          Markup, Paragraph, Panel, Tabs)
from bokeh.client import push_session
from bokeh.io import curdoc
from bokeh.io.state import curstate
from bokeh.palettes import RdYlGn5, RdYlGn7
from bokeh.embed import server_session
from bokeh.io import push_notebook
from bokeh.plotting import figure


logger = logging.getLogger()
logger.setLevel(logging.INFO)

FNULL = open(os.devnull, 'w')

#UTC_GPS_DIFFERENCE_SEC = 315964800
UTC_GPS_DIFFERENCE_SEC = 0 
O2_START = 1185580818
O2_END = 1188259218
O3a_START = 1238166018
O3a_END = 1253977218
O3b_START = 1256655618
O3b_END = 1269363618

from django.conf import settings
if 'staging' in str(settings):
    #O2_key = 'default'
    O2_key = 'O2'
    #O3a_key = 'default'	
    O3a_key = 'O3a'
    #O3b_key = 'default'
    O3b_key = 'O3b'

if 'local' in str(settings):
    O2_key = 'default'
    O3a_key = 'default'
    O3b_key = 'default'
    
def get_run(gps_min, gps_max):
    if (gps_min>=O2_START)&(gps_min<=O2_END) or (gps_max>=O2_START)&(gps_max<=O2_END) or (gps_min<=O2_START)&(gps_max>=O2_END):
        dbkey_ =  O2_key
    elif (gps_min>=O3a_START)&(gps_min<=O3a_END) or (gps_max>=O3a_START)&(gps_max<=O3a_END) or (gps_min<=O3a_START)&(gps_max>=O3a_END):
        dbkey_ =  O3a_key 
    elif (gps_min>=O3b_START)&(gps_min<=O3b_END) or (gps_max>=O3b_START)&(gps_max<=O3b_END) or (gps_min<=O3b_START)&(gps_max>=O3b_END):
        dbkey_ =  O3b_key
    else: 
        dbkey_ = 'default'  
    return dbkey_                            

class AsyncProcWrapper:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._p = None

    async def start(self):
        self._p = await asyncio.create_subprocess_exec(*self.args,
                                                       **self.kwargs)

    @property
    def p(self) -> aiosubprocess.Process:
        return self._p

    @property
    def stdin(self) -> aiosubprocess.streams.StreamWriter:
        return self.p.stdin

    @property
    def stdout(self) -> aiosubprocess.streams.StreamReader:
        return self.p.stdout

    @property
    def stderr(self) -> aiosubprocess.streams.StreamReader:
        return self.p.stderr

    @classmethod
    async def create(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        await obj.start()
        return obj

    async def communicate(self) -> List[bytes]:
        err = await self.stderr.read()
        out = await self.stdout.read()
        return out, err


async def async_subprocess(*args, **kwargs):
    return await AsyncProcWrapper.create(*args, **kwargs)


def make_ssh_subprocess(*tunnel_args):
    async def async_ssh_subprocess(*args, **kwargs):
        return await async_subprocess('ssh', *tunnel_args, '-tt',
                                      '{0}'.format(' '.join(args)), **kwargs)

    def ssh_subprocess(*args, **kwargs):
        return Popen(['ssh', *tunnel_args, '-tt',
                      '{0}'.format(' '.join(args[0]))], **kwargs)

    return async_ssh_subprocess, ssh_subprocess


class AsyncBytesIO(asyncio.streams.StreamReader, _pyio.BytesIO):
    def __init__(self):
        super().__init__()
        self._pos = 0
        self._alt_out = None

    def write(self, s):
        b = s.encode() if isinstance(s, str) else s
        self.feed_data(b)
        if self._alt_out:
            self._alt_out.write(s)

    @contextmanager
    def redirect_stdout(self, copy=False):
        stdout, sys.stdout = sys.stdout, self  # io.TextIOWrapper(self)
        if copy:
            self._alt_out = stdout
        yield
        sys.stdout = stdout

    async def read_all(self):
        await self._wait_for_data('updater')
        b = self.getvalue()
        self._buffer.clear()
        return b


class BokehConsole:
    def __init__(self, n=10, max_line_len=200, input_bottom=True):
        self.n = n
        self.max_line_len = max_line_len
        self.source = self.make_source()
        self.p = self.make_plot()
        self.line_buffer = deque(self.source.data['text'])
        self._rotate = 1 if not input_bottom else -1
        self._pos = 0 if not input_bottom else -1
        super(BokehConsole, self).__init__()

    def make_source(self):
        return ColumnDataSource({'text': [''] * self.n,
                                 'zeros': [0] * self.n,
                                 'line': list(reversed(range(self.n)))})

    def make_plot(self):
        p = figure(y_range=(Range1d(-1, self.n + 1)),
                   x_range=(Range1d(-2, self.max_line_len + 1)), tools='hover',
                   width=int(self.max_line_len * 6.35 + 160),
                   height=(self.n + 2) * 16 + 100)
        p.text('zeros', 'line', 'text', source=self.source)
        p.axis.visible = None
        p.toolbar_location = 'below'
        g = p.grid
        g.grid_line_color = '#FFFFFF'
        return p

    def _push_line(self, line):
        self.line_buffer.rotate(self._rotate)
        self.line_buffer[self._pos] = line
        self.source.data['text'] = list(self.line_buffer)

    def _push_lines(self, lines):
        l = len(lines)
        if self._pos == -1:  # lines come in from bottom
            for i, line in enumerate(lines):
                self.line_buffer[i] = line
            self.line_buffer.rotate(self._rotate * l)
        else:  # lines come in from top
            self.line_buffer.rotate(self._rotate * l)
            for i, line in enumerate(lines):
                self.line_buffer[i] = line
        self.source.data['text'] = list(self.line_buffer)

    def output_text(self, s):
        lines = list()
        for line in s.split('\n'):
            if not line:
                continue
            if len(line) <= self.max_line_len:
                lines.append(line)
            else:
                tokens = list()
                i = -1
                for token in line.split(' '):
                    i += 1 + len(token)
                    if i > self.max_line_len:
                        lines.append(' '.join(tokens))
                        tokens = [token]
                        i = len(token)
                    else:
                        tokens.append(token)
                lines.append(' '.join(tokens))
        self._push_lines(lines)


JobProgress = namedtuple('JobProgress', 'name percent state')
Command = namedtuple('Command', 'command args kwargs')

BytesStdOut = namedtuple('BytesStdOut', 'bytes')
TextStdOut = namedtuple('TextStdOut', 'text')
BytesStdErr = namedtuple('BytesStdErr', 'bytes')
TextStdErr = namedtuple('TextStdErr', 'text')


class ChangeStream(asyncio.Queue):
    def __init__(self, *args, loop=None, source_fun=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._loop = loop or asyncio.get_event_loop()
        self.sentinel2subscribers = defaultdict(list)
        notifier_init = partial(self.ChangeNotifier, self._loop)
        self.sentinel2notifier = defaultdict(notifier_init)
        self._terminating = False
        self.terminated = False
        self.source_fun = source_fun or (lambda source: None)

    class ChangeNotifier:
        def __init__(self, loop):
            """
            :param notify_classes: Change classes to trigger a wake-up
            :param loop:
            :return:
            """
            self._waiters = list()
            self._loop = loop
            self.change = None

        def __len__(self):
            return len(self._waiters)

        def __bool__(self):
            return bool(self._waiters)

        def wake_up(self, change):
            self.change = change
            self._wakeup_waiters()

        def _wakeup_waiters(self):
            waiters = self._waiters
            if waiters:
                for waiter in waiters:
                    if not waiter.cancelled():
                        waiter.set_result(None)
            waiters.clear()

        async def wait_for_change(self):
            waiter = asyncio.futures.Future(loop=self._loop)
            self._waiters.append(waiter)
            try:
                await waiter
                return self.change
            finally:
                if waiter in self._waiters:
                    self._waiters.remove(waiter)

    class BytesRedirecter:
        def __init__(self, change_stream: asyncio.Queue, copy_out,
                     wrap_class=BytesStdOut):
            self.change_stream = change_stream
            self._copy_out = copy_out
            self.wrap_class = wrap_class
            self.put_bytes = True if hasattr(wrap_class, 'bytes') else False

        def write(self, b):
            is_bytes = isinstance(b, bytes)
            # no change needed
            if (is_bytes and self.put_bytes) or (
                        not is_bytes and not self.put_bytes):
                self.change_stream.put_nowait(self.wrap_class(b))

            # is bytes, but should be str
            elif is_bytes:
                self.change_stream.put_nowait(self.wrap_class(b.decode()))

            # is not bytes, but should be
            else:
                self.change_stream.put_nowait(self.wrap_class(b.encode()))

            if self._copy_out:
                self._copy_out.write(b)

        def flush(self):
            if self._copy_out:
                self._copy_out.flush()

    class TextRedirecter:
        def __init__(self, change_stream: asyncio.Queue, copy_out,
                     wrap_class=TextStdOut):
            self.change_stream = change_stream
            self._copy_out = copy_out
            self.wrap_class = wrap_class
            self.put_str = True if hasattr(wrap_class, 'text') else False

        def write(self, s):
            is_text = isinstance(s, str)
            # no change needed
            if (is_text and self.put_str) or (not is_text and not self.put_str):
                self.change_stream.put_nowait(self.wrap_class(s))

            # is bytes, but should be str
            elif not is_text:
                self.change_stream.put_nowait(self.wrap_class(s.decode()))

            # is not bytes, but should be
            else:
                self.change_stream.put_nowait(self.wrap_class(s.encode()))

            if self._copy_out:
                self._copy_out.write(s)

        def flush(self):
            if self._copy_out:
                self._copy_out.flush()

    @contextmanager
    def redirect_stdout(self, copy=False, out_type=str, **kwargs):
        if copy:
            copy_out = sys.stdout
        else:
            copy_out = None

        if out_type is str:
            redirecter = self.TextRedirecter(self, copy_out, **kwargs)
        else:
            redirecter = self.BytesRedirecter(self, copy_out, **kwargs)

        stdout, sys.stdout = sys.stdout, redirecter  # io.TextIOWrapper(self)
        yield
        sys.stdout = stdout

    @contextmanager
    def redirect_stderr(self, copy=False, out_type=str, **kwargs):
        if copy:
            copy_out = sys.stdout
        else:
            copy_out = None

        if out_type is str:
            if 'wrap_class' not in kwargs:
                kwargs['wrap_class'] = TextStdErr
            redirecter = self.TextRedirecter(self, copy_out, **kwargs)
        else:
            if 'wrap_class' not in kwargs:
                kwargs['wrap_class'] = BytesStdErr
            redirecter = self.BytesRedirecter(self, copy_out, **kwargs)

        stdout, sys.stderr = sys.stderr, redirecter  # io.TextIOWrapper(self)
        yield
        sys.stderr = stdout

    async def wait_for_change(self, *sentinels):
        sentinel = tuple(
            sorted(sentinels, key=lambda klass: klass.__qualname__))
        return await self.sentinel2notifier[sentinel].wait_for_change()

    def register_subscriber(self, waiter_coro):
        if inspect.isfunction(waiter_coro):
            waiter_coro = waiter_coro()
        sentinel = next(waiter_coro)
        self.sentinel2subscribers[sentinel].append(waiter_coro)

    async def start(self):
        if self.terminated:
            warnings.warn(
                'Trying to start a terminated {}'.format(self.__class__))
            return

        while True:
            change = await self.get()
            a = 'hej'
            for sentinel, waiters in self.sentinel2subscribers.items():
                if isinstance(change, sentinel):
                    dead_waiters = list()
                    for waiter in waiters:
                        try:
                            source = waiter.send(change)
                            if source:
                                self.source_fun(source)
                        except StopIteration:
                            dead_waiters.append(waiter)
                    for waiter in dead_waiters:
                        waiters.remove(waiter)

            for sentinel, notifier in self.sentinel2notifier.items():
                if isinstance(change, sentinel):
                    notifier.wake_up(change)

            if isinstance(change, Command):
                if change.command == 'terminate':
                    self._terminating = False
                    self.terminated = True
                    while not self.empty():
                        self.get_nowait()
                    self._unfinished_tasks = 0
                    self.sentinel2subscribers.clear()
                    return

    async def terminate(self):
        if self.terminated:
            return
        if not self._terminating:
            self._terminating = True
            await self.put(Command('terminate', (), ()))

        while self._terminating:
            await self.wait_for_change(Command)
        assert self.terminated


@contextmanager
def redirect_to_changestream(change_stream: asyncio.Queue, err=False):
    stdout = sys.stdout


# Unless explicitly defined as Nvidia device all GPUs are considered as cuda
# devices
CPU = namedtuple('CPU', 'dev load')
GPU = namedtuple('GPU', 'dev free nvdev')
GPUNv = namedtuple('GPUNv', 'nvdev free load')  # <- nvidia device
GPUComb = namedtuple('GPUComb', 'dev free load')

GPUProcess = namedtuple('GPUProcess', 'pid owner dev memusage')
GPUNvProcess = namedtuple('GPUNvProcess',
                          'nvdev pid memusage')  # <- nvidia device

nvgpu_used_tot_load = re.compile('(\d+)MiB / (\d+)MiB \|\W*(\d+)%')
nvgpu_nvdev = re.compile('\|\W*(\d+)[^\|]+\|\W*[\dA-F]+:[\dA-F]+:[\dA-F]+\.')
nvgpu_divider = re.compile('^\+(-+\+)+\n?$')

gpu_dev_nvdev_used_tot = re.compile(
    'Device  (\d).*nvidia-smi\W*(\d+).+ (\d+) of (\d+) MiB Used')

gpu_nvdev_pid_mem = re.compile('(\d+)\W*(\d+).+?(\d+)MiB \|\n?$')

cpu_dev_load = re.compile('%Cpu(\d+)\W*:.*?(\d+)\[')
cpu_dev_us_sy = re.compile('%Cpu(\d+)\W*:\W* (\d+\.\d+) us,\W+(\d+\.\d+)')


def nv_line2nvdev(line, prev_nvdev=None):
    if nvgpu_divider.match(line):
        return None

    res = nvgpu_nvdev.findall(line)
    return int(res[0]) if res else prev_nvdev


def nv_line2GPUNv(line, nvdev):
    res = nvgpu_used_tot_load.findall(line)
    if res:
        if nvdev is None:
            raise ValueError('Found a valid info line, but i have no device')
        used, tot, load = res[0]
        free = int(tot) - int(used)
        return GPUNv(nvdev, free, float(load))


def nv_line2GPUNvProcess(line):
    res = gpu_nvdev_pid_mem.findall(line)
    if not res:
        return None
    return GPUNvProcess(*(int(r) for r in res[0]))


def cuda_line2GPU(line) -> GPU:
    res = gpu_dev_nvdev_used_tot.findall(line)
    if not res:
        return None
    dev, nvdev, used, tot = res[0]
    free = int(tot) - int(used)
    return GPU(int(dev), free, int(nvdev))


def lines2CPUs(lines):
    if not isinstance(lines, str):
        lines = '\n'.join(lines)
    res = cpu_dev_load.findall(lines)
    if res:
        return [CPU(int(dev), float(load)) for dev, load in res]

    res = cpu_dev_us_sy.findall(lines)
    if res:
        return [CPU(int(dev), float(us) + float(sy)) for dev, us, sy in res]
    return []


class RessourceMonitor:
    def __init__(self, change_stream: ChangeStream,
                 async_exec=async_subprocess,
                 normal_exec=Popen):
        # self.sources = self.init_sources()
        self.async_exec = async_exec
        self.normal_exec = normal_exec
        self.change_stream = change_stream
        self.monitors = OrderedDict()
        self.terminated = False
        self._terminating = False

    def init_sources(self):
        _gpus = self.gpus_mem()
        _cpus = self.cpus()

        source = dict(cpu=ColumnDataSource({
            'cpu_dev': [gpu.dev for gpu in _cpus],
            'cpu_load': [gpu.load for gpu in _cpus]}),
            gpumem=ColumnDataSource({
                'gpu_dev': [gpu.dev for gpu in _gpus],
                'gpu_free': [gpu.free for gpu in _gpus],
            }),
            gpuclock=ColumnDataSource({
                'gpu_dev': [gpu.dev for gpu in _gpus],
                'gpu_load': [gpu.free for gpu in _gpus],
            }))
        return source

    async def terminate(self):
        if self.terminated:
            return
        if not self._terminating:
            self._terminating = True
        while self.monitors:
            await self.change_stream.wait_for_change(self.__class__)
        self._terminating, self.terminated = False, True

    @contextmanager
    def register_mon(self, *sentinels):
        id = hash(random.random())
        self.monitors[id] = sentinels
        yield
        del self.monitors[id]

    def mon_decorator(*sentinels):
        if sentinels and isinstance(sentinels[0], asyncio.Queue):
            sentinels = sentinels[1:]
        if not sentinels:
            raise ValueError('Cannot define a monitor without a sentinel')

        def decorator(func):
            @wraps(func)
            async def wrapper(instance, *args, **kwargs):
                if instance.terminated or instance._terminating:
                    warnings.warn('Trying to start a terminated {}'.format(
                        instance.__class__))
                    return
                with instance.register_mon(*sentinels):
                    await func(instance, *args, **kwargs)

            return wrapper

        return decorator

    @mon_decorator(CPU)
    async def cpus_mon(self):
        subproc_exec = self.async_exec
        p = await subproc_exec('top', '-b', '-p0', '-d3',
                               stdout=PIPE)
        cpus = dict()
        while not self._terminating:
            line = (await p.stdout.readline()).decode()
            cpu = lines2CPUs(line)
            if cpu:
                cpu = cpu[0]
                prev_load = cpus.get(cpu.dev, None)
                if prev_load != cpu.load:
                    cpus[cpu.dev] = cpu.load
                    await self.change_stream.put(cpu)
        await self.change_stream.put(self)

    @mon_decorator(GPUComb, GPUProcess)
    async def gpus_mon(self, loop: asyncio.BaseEventLoop = None,
                       ignore=tuple()):
        subproc_exec = self.async_exec
        nv2cuda, pid2owner = await asyncio.gather(
            self.nv2cuda_coro(subproc_exec),
            self.pid2owner_coro(subproc_exec))

        async def start_proc():
            return (await self.async_exec('nvidia-smi', '-l', '2',
                                          stdout=asyncio.subprocess.PIPE,
                                          stderr=FNULL))

        p = await start_proc()

        loop = loop or asyncio.get_event_loop()
        gpus = dict()
        gpu_nvprocs = dict()
        do_GPUComb = GPUComb not in ignore
        do_GPUProcess = GPUProcess not in ignore
        nvdev = None
        tasks = list()
        seen_pids = list()
        last_update = time.time()
        while not self._terminating:
            line = await p.stdout.readline()
            if p.stdout.at_eof():
                warnings.warn('nvidia-smi died..  restarting')
                p = await start_proc()
                warnings.warn('nvidia-smi restarted')
            line = line.decode()
            if do_GPUComb:
                nvdev = nv_line2nvdev(line, nvdev)
                nvgpu = nv_line2GPUNv(line, nvdev)

                # a gpu was found in stdout
                if nvgpu:
                    prev_gpu = gpus.get(nvgpu.nvdev, None)
                    # has anything changed? (also update at least ever 10 sec)
                    if prev_gpu != nvgpu[1:] or time.time() - last_update > 10:
                        last_update = time.time()

                        # translate to cuda dev and update gpus
                        gpu = GPUComb(nv2cuda[nvgpu.nvdev], *nvgpu[1:])
                        gpus[nvgpu.nvdev] = nvgpu[1:]

                        # put into change stream
                        await self.change_stream.put(gpu)
                    continue

            if do_GPUProcess:
                nvproc = nv_line2GPUNvProcess(line)
                if nvproc:
                    seen_pids.append(nvproc.pid)
                    tasks.append(
                        loop.create_task(self._nvproc2proc(subproc_exec,
                                                           nvproc,
                                                           pid2owner,
                                                           nv2cuda,
                                                           gpu_nvprocs)))
                    continue

            if tasks:
                await asyncio.wait(tasks)
                tasks.clear()

                dead_pids = set(gpu_nvprocs.keys()).difference(seen_pids)
                for dead_proc in (gpu_nvprocs[pid] for pid in dead_pids):
                    await self.change_stream.put(GPUProcess(dead_proc.pid,
                                                            pid2owner[
                                                                dead_proc.pid],
                                                            nv2cuda[
                                                                dead_proc.nvdev],
                                                            0))
                    gpu_nvprocs.pop(dead_proc.pid)
                seen_pids.clear()
        await self.change_stream.put(self)

    @staticmethod
    def gpus_mem(subproc_exec=Popen) -> List[GPU]:
        _gpus = list()
        for line in subproc_exec(['cuda-smi'],
                                 stdout=PIPE).stdout.read().decode(
            'utf8').split('\n')[:-1]:
            gpu = cuda_line2GPU(line)
            if gpu:
                _gpus.append(gpu)
        return _gpus

    @staticmethod
    async def gpus_mem_coro(subproc_exec=async_subprocess):
        p = await subproc_exec('cuda-smi',
                               stdout=asyncio.subprocess.PIPE,
                               stderr=FNULL)

        data = await p.stdout.read()
        _gpus = list()
        for line in data.decode('utf8').split('\n'):
            gpu = cuda_line2GPU(line)
            if gpu:
                _gpus.append(gpu)
        return _gpus

    @staticmethod
    def nv_gpus_mem_load(subproc_exec=Popen) -> List[GPUNv]:
        _gpus = list()
        nvdev = None
        for line in subproc_exec(['nvidia-smi'],
                                 stdout=PIPE).stdout.read().decode(
            'utf8').split('\n')[:-1]:
            nvdev = nv_line2nvdev(line, nvdev)
            gpu = nv_line2GPUNv(line, nvdev)
            if gpu:
                _gpus.append(gpu)
        return _gpus

    @staticmethod
    async def nv_gpus_mem_load_coro(subproc_exec=async_subprocess) -> List[
        GPUNv]:
        p = await subproc_exec(['nvidia-smi'],
                               stdout=PIPE)
        data = await p.stdout.read()
        _gpus = list()
        nvdev = None
        for line in data.decode('utf8').split('\n'):
            nvdev = nv_line2nvdev(line, nvdev)
            gpu = nv_line2GPUNv(line, nvdev)
            if gpu:
                _gpus.append(gpu)
        return _gpus

    @classmethod
    def nv2cuda(cls, subproc_exec=Popen):
        gpus = cls.gpus_mem(subproc_exec)
        return dict((gpu.nvdev, gpu.dev) for gpu in gpus)

    @classmethod
    async def nv2cuda_coro(cls, subproc_exec=async_subprocess):
        gpus = await cls.gpus_mem_coro(subproc_exec)
        return dict((gpu.nvdev, gpu.dev) for gpu in gpus)

    @classmethod
    def gpus_comb(cls, subproc_exec=Popen):
        nv2cuda = cls.nv2cuda(subproc_exec)
        nvgpus = cls.nv_gpus_mem_load(subproc_exec)
        return [GPUComb(nv2cuda[gpu.nvdev], *gpu[1:]) for gpu in nvgpus]

    @classmethod
    async def gpus_comb_coro(cls, subproc_exec=async_subprocess):
        nv2cuda, nvgpus = await asyncio.gather(cls.nv2cuda_coro(subproc_exec),
                                               cls.nv_gpus_mem_load_coro(
                                                   subproc_exec))

        return [GPUComb(nv2cuda[gpu.nvdev], *gpu[1:]) for gpu in nvgpus]

    @classmethod
    def gpu_procs(cls, subproc_exec=Popen):
        nv2cuda = cls.nv2cuda(subproc_exec)
        nvprocs = dict()
        for line in subproc_exec(['nvidia-smi'],
                                 stdout=PIPE).stdout.read().decode(
            'utf8').split('\n')[:-1]:
            proc = nv_line2GPUNvProcess(line)
            if proc:
                nvprocs[proc.pid] = proc

        procs = list()
        for nvproc, owner in zip(nvprocs.values(),
                                 cls.find_pid_owner(*nvprocs.keys(),
                                                    subproc_exec=subproc_exec)):
            procs.append(GPUProcess(nvproc.pid, owner, nv2cuda[nvproc.nvdev],
                                    nvproc.memusage))
        return procs

    @classmethod
    async def gpu_procs_coro(cls, subproc_exec=async_subprocess):
        nv2cuda, p = await asyncio.gather(cls.nv2cuda_coro(subproc_exec),
                                          subproc_exec(['nvidia-smi'],
                                                       stdout=PIPE))
        data = await p.stdout.read()
        nvprocs = dict()
        for line in data.decode(
                'utf8').split('\n')[:-1]:

            proc = nv_line2GPUNvProcess(line)
            if proc:
                nvprocs[proc.pid] = proc

        procs = list()
        owners = await cls.find_pid_owner_coro(nvprocs.keys(), subproc_exec)
        for nvproc, owner in zip(nvprocs.values(), owners):
            procs.append(GPUProcess(nvproc.pid, owner, nv2cuda[nvproc.nvdev],
                                    nvproc.memusage))
        return procs

    async def _nvproc2proc(self, subproc_exec, nvproc: GPUNvProcess,
                           pid2owner: dict, nv2cuda: dict, gpu_nvprocs: dict):
        if nvproc.pid not in pid2owner:
            owner = await self.find_pid_owner_coro(nvproc.pid,
                                                   subproc_exec=subproc_exec)
            owner = owner[0]
            pid2owner[nvproc.pid] = owner
            prev_proc = None
        else:
            owner = pid2owner[nvproc.pid]
            prev_proc = gpu_nvprocs.get(nvproc.pid, None)

        if prev_proc != nvproc:
            gpu_nvprocs[nvproc.pid] = nvproc
            proc = GPUProcess(nvproc.pid, owner, nv2cuda[nvproc.nvdev],
                              nvproc.memusage)
            await self.change_stream.put(proc)

    @staticmethod
    def cpus(subproc_exec=Popen):
        p = subproc_exec(['top', '-n2', '-b', '-p0'], stdout=PIPE, stderr=FNULL)
        data = p.stdout.read()
        devices = set()
        for cpu in reversed(lines2CPUs(data.decode())):
            if cpu.dev not in devices:
                yield cpu
                devices.add(cpu.dev)

    @staticmethod
    async def cpus_coro(subproc_exec=async_subprocess):
        p = await subproc_exec('top', '-n2', '-b',
                               stdout=asyncio.subprocess.PIPE,
                               stderr=FNULL)
        data = await p.stdout.read()
        return lines2CPUs(data.decode())

    @staticmethod
    def find_pid_owner(*pids, subproc_exec=Popen):
        if not pids:
            return list()
        pids = list(str(pid) for pid in pids)
        pid_cs = ','.join(pids)
        p = subproc_exec(['ps', '-p', pid_cs, '-o', 'pid,user', 'h'],
                         stdout=PIPE,
                         stderr=PIPE)
        data, err = p.communicate()
        if err and not re.match(b'^Connection to localhost closed.\r?\n$', err):
            raise IOError(err)
        pid2owner = dict(re.findall('\W*(\d+) (\w+)', data.decode()))
        return [pid2owner.get(pid, None) for pid in pids]

    @staticmethod
    async def find_pid_owner_coro(*pids, subproc_exec=async_subprocess):
        pids = list(str(pid) for pid in pids)
        pid_cs = ','.join(pids)
        p = await subproc_exec('ps', '-p', pid_cs, '-o', 'pid,user', 'h',
                               stdout=PIPE,
                               stderr=PIPE)

        data, err = await p.communicate()
        if err and not re.match(b'^Connection to localhost closed.\r?\n$', err):
            raise IOError(err)
        pid2owner = dict(re.findall('\W*(\d+) (\w+)', data.decode()))
        return [pid2owner.get(pid, None) for pid in pids]

    @staticmethod
    def pid2owner(subproc_exec=Popen):
        p = subproc_exec('ps', '-A', '-o', 'pid,user', 'h',
                         stdout=PIPE,
                         stderr=PIPE)
        data, err = p.communicate()
        if err and not re.match(b'^Connection to localhost closed.\r?\n$', err):
            raise IOError(err)
        pid2owner = dict((int(pid), owner) for pid, owner in
                         re.findall('\W*(\d+) (\w+)', data.decode()))
        return pid2owner

    @staticmethod
    async def pid2owner_coro(subproc_exec=async_subprocess):
        p = await subproc_exec('ps', '-A', '-o', 'pid,user', 'h',
                               stdout=PIPE,
                               stderr=PIPE)
        data, err = await p.communicate()
        if err and not re.match(b'^Connection to localhost closed.\r?\n$', err):
            raise IOError(err)
        pid2owner = dict((int(pid), owner) for pid, owner in
                         re.findall('\W*(\d+) (\w+)', data.decode()))
        return pid2owner


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser('HPC monitor')
    parser.add_argument('-b', '--bokeh-port', type=int, default=5006,
                        dest='bp')
    parser.add_argument('-m', '--monitor-port', type=int, default=8080,
                        dest='mp', help='the port the monitor will serve '
                                        'the web interface on')
    parser.add_argument('-r', '--remote-only', action='store_true',
                        help='if specified, only hosts specifiend in --tunnels'
                             'will be monitored. Else this machine is also'
                             'monitored')

    parser.add_argument('-t', '--tunnels', type=str, default=None, nargs='*',
                        help='specify tunnels to monitored hosts.'
                             'for special args encapsulate args to ssh with ""'
                             'If not specified just monitor this machine')

    parser.add_argument('-p', '--plots', type=str, default=None, nargs='*',
                        help='specify specific plots in stead of defaults')

    args = parser.parse_args()
    standalone(*args.tunnels, plots=args.plots, remote_only=args.remote_only,
               bokeh_port=args.bp, mon_port=args.mp)
