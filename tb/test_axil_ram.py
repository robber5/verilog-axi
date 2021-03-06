#!/usr/bin/env python
"""

Copyright (c) 2018 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from myhdl import *
import os

import axil

module = 'axil_ram'
testbench = 'test_%s' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    DATA_WIDTH = 32
    ADDR_WIDTH = 16
    STRB_WIDTH = int(DATA_WIDTH/8)

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    axil_awaddr = Signal(intbv(0)[ADDR_WIDTH:])
    axil_awprot = Signal(intbv(0)[3:])
    axil_awvalid = Signal(bool(0))
    axil_wdata = Signal(intbv(0)[DATA_WIDTH:])
    axil_wstrb = Signal(intbv(0)[STRB_WIDTH:])
    axil_wvalid = Signal(bool(0))
    axil_bready = Signal(bool(0))
    axil_araddr = Signal(intbv(0)[ADDR_WIDTH:])
    axil_arprot = Signal(intbv(0)[3:])
    axil_arvalid = Signal(bool(0))
    axil_rready = Signal(bool(0))

    # Outputs
    axil_awready = Signal(bool(0))
    axil_wready = Signal(bool(0))
    axil_bresp = Signal(intbv(0)[2:])
    axil_bvalid = Signal(bool(0))
    axil_arready = Signal(bool(0))
    axil_rdata = Signal(intbv(0)[DATA_WIDTH:])
    axil_rresp = Signal(intbv(0)[2:])
    axil_rvalid = Signal(bool(0))

    # AXI4-Lite master
    axil_master_inst = axil.AXILiteMaster()
    axil_master_pause = Signal(bool(False))

    axil_master_logic = axil_master_inst.create_logic(
        clk,
        rst,
        m_axil_awaddr=axil_awaddr,
        m_axil_awprot=axil_awprot,
        m_axil_awvalid=axil_awvalid,
        m_axil_awready=axil_awready,
        m_axil_wdata=axil_wdata,
        m_axil_wstrb=axil_wstrb,
        m_axil_wvalid=axil_wvalid,
        m_axil_wready=axil_wready,
        m_axil_bresp=axil_bresp,
        m_axil_bvalid=axil_bvalid,
        m_axil_bready=axil_bready,
        m_axil_araddr=axil_araddr,
        m_axil_arprot=axil_arprot,
        m_axil_arvalid=axil_arvalid,
        m_axil_arready=axil_arready,
        m_axil_rdata=axil_rdata,
        m_axil_rresp=axil_rresp,
        m_axil_rvalid=axil_rvalid,
        m_axil_rready=axil_rready,
        pause=axil_master_pause,
        name='master'
    )

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,

        s_axil_awaddr=axil_awaddr,
        s_axil_awprot=axil_awprot,
        s_axil_awvalid=axil_awvalid,
        s_axil_awready=axil_awready,
        s_axil_wdata=axil_wdata,
        s_axil_wstrb=axil_wstrb,
        s_axil_wvalid=axil_wvalid,
        s_axil_wready=axil_wready,
        s_axil_bresp=axil_bresp,
        s_axil_bvalid=axil_bvalid,
        s_axil_bready=axil_bready,
        s_axil_araddr=axil_araddr,
        s_axil_arprot=axil_arprot,
        s_axil_arvalid=axil_arvalid,
        s_axil_arready=axil_arready,
        s_axil_rdata=axil_rdata,
        s_axil_rresp=axil_rresp,
        s_axil_rvalid=axil_rvalid,
        s_axil_rready=axil_rready
    )

    @always(delay(4))
    def clkgen():
        clk.next = not clk

    def wait_normal():
        while not axil_master_inst.idle():
            yield clk.posedge

    def wait_pause_master():
        while not axil_master_inst.idle():
            axil_master_pause.next = True
            yield clk.posedge
            yield clk.posedge
            yield clk.posedge
            axil_master_pause.next = False
            yield clk.posedge

    @instance
    def check():
        yield delay(100)
        yield clk.posedge
        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge
        yield delay(100)
        yield clk.posedge

        # testbench stimulus

        yield clk.posedge
        print("test 1: read and write")
        current_test.next = 1

        addr = 4
        test_data = b'\x11\x22\x33\x44'

        axil_master_inst.init_write(addr, test_data)

        yield axil_master_inst.wait()
        yield clk.posedge

        axil_master_inst.init_read(addr, len(test_data))

        yield axil_master_inst.wait()
        yield clk.posedge

        data = axil_master_inst.get_read_data()
        assert data[0] == addr
        assert data[1] == test_data

        yield delay(100)

        yield clk.posedge
        print("test 2: various reads and writes")
        current_test.next = 2

        for length in range(1,8):
            for offset in range(4,8):
                for wait in wait_normal, wait_pause_master:
                    print("length %d, offset %d"% (length, offset))
                    addr = 256*(16*offset+length)+offset
                    test_data = b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

                    axil_master_inst.init_write(addr-4, b'\xAA'*(length+8))

                    yield axil_master_inst.wait()

                    axil_master_inst.init_write(addr, test_data)

                    yield wait()

                    axil_master_inst.init_read(addr-1, length+2)

                    yield axil_master_inst.wait()

                    data = axil_master_inst.get_read_data()
                    assert data[0] == addr-1
                    assert data[1] == b'\xAA'+test_data+b'\xAA'

        for length in range(1,8):
            for offset in range(4,8):
                for wait in wait_normal, wait_pause_master:
                    print("length %d, offset %d"% (length, offset))
                    addr = 256*(16*offset+length)+offset
                    test_data = b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

                    axil_master_inst.init_write(addr, test_data)

                    yield axil_master_inst.wait()

                    axil_master_inst.init_read(addr, length)

                    yield wait()
                    yield clk.posedge

                    data = axil_master_inst.get_read_data()
                    assert data[0] == addr
                    assert data[1] == test_data

        yield delay(100)

        raise StopSimulation

    return instances()

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
