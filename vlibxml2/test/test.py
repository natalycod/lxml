import gc, pprint
import time
import sys
import unittest
import vlibxml2
import vlibxml2_mod
import cStringIO
from vlibxml2 import victree

vlibxml2_mod.debugMode = False

class TestXmlNode(unittest.TestCase):

    def setUp(self):
        vlibxml2.initParser()
        vlibxml2.debugMemory(True)

    def tearDown(self):
        # The XML parser seems to use a fixed amount of memory - 422 bytes.
        assert 422 >= vlibxml2.debugMemory(1)
        self.assertEquals(vlibxml2.nodecache.size(), 0)

    def testEmptyDoc( self ):
        doc = vlibxml2.newDoc('1.0')
        self.assertEquals( str(doc), '''<?xml version="1.0"?>\n''' )


    def testSimpleNode(self):
        node = vlibxml2.newNode('foo')
        assert str(node) == '<foo/>'
        self.assertEquals(node.name(), 'foo')

        node.setName('bar')
        self.assertEquals(node.name(), 'bar')

    def testRootNode1( self ):

        # set the root element for a doc with no elements
        doc = vlibxml2.newDoc('1.0')
        foo = vlibxml2.newNode('foo')
        doc.setRootElement(foo)
        r1 = doc.rootElement()
        assert r1 == foo
        self.assertEquals( str(doc), '''<?xml version="1.0"?>\n<foo/>\n''' )

    def testRootNode2(self):
        # set the root element for a doc with an element that has no reference
        # to it other than the doc node
        doc = vlibxml2.newDoc('1.0')
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        doc.setRootElement(foo)
        del foo
        doc.setRootElement(bar)

        self.assertEquals(bar, doc.rootElement())
        self.assertEquals( str(doc), '''<?xml version="1.0"?>\n<bar/>\n''' )

    def testRootNode3(self):
        # set the root element for a doc with an element that has at least one
        # other reference to it
        doc = vlibxml2.newDoc('1.0')
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        doc.setRootElement(foo)
        doc.setRootElement(bar)

        self.assertEquals(bar, doc.rootElement())
        self.assertEquals( str(doc), '''<?xml version="1.0"?>\n<bar/>\n''' )



    def testSimpleNode(self):
        foo = vlibxml2.newNode('foo')


class TestBuggyStill(unittest.TestCase):

    def setUp(self):
        vlibxml2.debugMemory(True)

    def tearDown(self):
        bytesUsed  =vlibxml2.debugMemory(1)
        if bytesUsed <> 422:
            print "Using %d bytes of memory." % vlibxml2.debugMemory(1)
        assert 422 >= vlibxml2.debugMemory(1)
        vlibxml2.nodecache.dumpCache()
        self.assertEquals(vlibxml2.nodecache.size(), 0)

    def testAddChild(self):
        foo = vlibxml2.newNode('foo')

        bar = vlibxml2.newNode('bar')
        baz = vlibxml2.newNode('baz')
        foo.addChild(bar)
        foo.addChild(baz)
        assert len(foo.children()) == 2
        assert bar in foo.children()
        assert baz in foo.children()

    def testParent(self):
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        baz = vlibxml2.newNode('baz')
        foo.addChild(bar)
        foo.addChild(baz)
        assert bar.parent() == foo
        assert baz.parent() == foo

    def testNoParent(self):
        foo = vlibxml2.newNode('foo')
        assert foo.parent() == None

    def testNextNode(self):
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        baz = vlibxml2.newNode('baz')
        foo.addChild(bar)
        foo.addChild(baz)
        assert bar.next() == baz
        assert foo.next() == None
        assert baz.next() == None

    def testPrevNode(self):
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        baz = vlibxml2.newNode('baz')
        foo.addChild(bar)
        foo.addChild(baz)
        assert bar.prev() == None
        assert foo.prev() == None
        assert baz.prev() == bar

    def testRenderNode(self):
        '''
        just render a node.  I'm not sure that this feature should really be
        supported.
        '''
        foo = vlibxml2.newNode('foo')
        self.assertEquals(str(foo), "<foo/>")

    def testNodeAttrs(self):
        '''
        test that node's can have attributes set properly
        '''
        foo = vlibxml2.newNode('foo')
        foo.setProp('abc', '123')
        self.assertEquals(str(foo), '''<foo abc="123"/>''')

    def testContent(self):
        '''
        test that node's can have content set
        '''
        foo = vlibxml2.newNode('foo')
        foo.setContent('abc')
        self.assertEquals(str(foo), '''<foo>abc</foo>''')

    def testParseDoc(self):
        '''
        test that basic parseDoc function works
        '''
        fragment = '<foo>foo<bar>bar</bar></foo>'
        doc = vlibxml2.parseDoc( fragment )
        nodes = [(str(node), node.type()) for node in doc.rootElement().children()]
        assert nodes == [('foo', 3), ('<bar>bar</bar>', 1)]

        for i in xrange(2000):
            fragment = '<foo%d>foo<bar>bar</bar></foo%d>' % (i, i)
            doc = vlibxml2.parseDoc( fragment )

    def testAccessMissingProp(self):
        '''
        Accessing a property/attribute that doesn't exist on a node should return None
        '''
        n = vlibxml2.newNode('foo')
        self.assertEquals(n.prop('notHere'), None)

    def testProperties(self):
        fragment = '<foo a="1" b="2"/>'
        doc = vlibxml2.parseDoc( fragment )

        rootElem = doc.rootElement()
        self.assertEquals(len(rootElem.properties()), 2)
        assert rootElem.properties()['a'] == '1'
        assert rootElem.properties()['b'] == '2'


    ### Start XPath tests
    def testXPath0(self):
        '''
        test basic xpath. Modelled after libxml2's node.xpathEval(expr) method
        '''
        doc = vlibxml2.newDoc('1.0')
        foo = vlibxml2.newNode('foo')
        doc.setRootElement(foo)
        bar = vlibxml2.newNode('bar')
        foo.addChild(bar)
        nodes = doc.xpathEval('//fub')
        assert len(nodes) == 0

    def testXPath1(self):
        '''
        test basic xpath. Modelled after libxml2's node.xpathEval(expr) method
        '''
        doc = vlibxml2.newDoc('1.0')
        foo = vlibxml2.newNode('foo')
        doc.setRootElement(foo)
        bar = vlibxml2.newNode('bar')
        foo.addChild(bar)
        nodes = doc.xpathEval('//foo')
        assert len(nodes) == 1
        assert nodes[0] == foo

    def testXPath2(self):
        '''
        test basic xpath selecting all nodes. Modelled after libxml2's node.xpathEval(expr) method
        '''
        doc = vlibxml2.newDoc('1.0')
        foo = vlibxml2.newNode('foo')
        doc.setRootElement(foo)
        bar = vlibxml2.newNode('bar')
        foo.addChild(bar)
        nodes = doc.xpathEval('//*')
        assert len(nodes) == 2
        assert foo in nodes
        assert bar in nodes

    def testXPathElem0(self):
        docstr = '''
        <foo>
            <bar id="1">
                bar 1 text
            </bar>
            <bar id="2">
                <batz>
                    batz text
                </batz>
            </bar>
            <bar id="3">
                bar 3 text
            </bar>
        </foo>
        '''

        doc = vlibxml2.parseDoc(docstr)
        assert len(doc.xpathEval("//bar")) == 3

    def testXPathByName(self):
        docstr = '''
        <foo>
            <bar id="1">
                bar 1 text
            </bar>
            <bar id="2">
                <batz>
                    batz text
                </batz>
            </bar>
            <bar id="3">
                bar 3 text
            </bar>
        </foo>
        '''

        doc= vlibxml2.parseDoc(docstr)
        self.assertEquals(len(doc.xpathEval('//batz')), 1)
        self.assertEquals(len(doc.xpathEval('//batz')), 1)
        self.assertEquals( doc.xpathEval('//batz')[0].content().strip(), 'batz text')


    def testNestingXPath(self):
        ''' test xpath on an xpath result '''
        doc = '''
        <foo>
            <bar id="1">
                bar 1 text
            </bar>
            <bar id="2">
                <batz>
                    batz text
                </batz>
            </bar>
            <bar id="3">
                bar 3 text
            </bar>
        </foo>
        '''
        doc = vlibxml2.parseDoc(doc)
        bars = doc.xpathEval('//bar')
        assert len(bars) == 3
        self.assertEquals( doc.xpathEval('//bar')[1].xpathEval('batz')[0].content().strip(), 'batz text')

    def testGetTitles(self):
        doc = vlibxml2.parseDoc(open('data/chromewaves.xml').read())
        self.assertEquals(len(doc.xpathEval('//title')), 11)

    ### End XPath tests



class TestReplaceNode(unittest.TestCase):

    def setUp(self):
        vlibxml2.initParser()
        vlibxml2.debugMemory(True)

    def tearDown(self):
        # The XML parser seems to use a fixed amount of memory - 422 bytes.
        assert 422 >= vlibxml2.debugMemory(1)
        self.assertEquals(vlibxml2.nodecache.size(), 0)

    def testEmptyDoc( self ):
        doc = vlibxml2.newDoc('1.0')
        self.assertEquals( str(doc), '''<?xml version="1.0"?>\n''' )

    def testReplaceNode0(self):
        '''
        Test the simple case of replacing a node with another node
        '''
        bar = vlibxml2.newNode('bar')
        baz = vlibxml2.newNode('baz')

        bar.replaceNode(baz)
        assert str(bar) == '<baz/>'
        self.assertEquals(bar.name(), 'baz')
        self.assertEquals(baz.name(), 'baz')


    def testReplaceNode1(self):
        '''
        Test the case of replacing a node with another node in a document with at least 1 node
        '''
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        foo.addChild(bar)
        baz = vlibxml2.newNode('baz')

        bar.replaceNode(baz)
        assert str(bar) == '<baz/>'


        self.assertEquals(foo.name(), 'foo')
        self.assertEquals(bar.name(), 'baz')
        self.assertEquals(baz.name(), 'baz')

    def testReplaceNode2(self):
        '''
        Test the case of replacing a next sibling node
        '''
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        baz = vlibxml2.newNode('baz')
        boo = vlibxml2.newNode('boo')

        foo.addChild(baz)
        foo.addChild(bar)

        bar.replaceNode(boo)
        self.assertEquals(str(bar), '<boo/>')
        self.assertEquals(foo.children(), [baz, boo])

        self.assertEquals(foo.name(), 'foo')
        self.assertEquals(bar.name(), 'boo')
        self.assertEquals(baz.name(), 'baz')
        self.assertEquals(boo.name(), 'boo')

    def testReplaceNode3(self):
        '''
        Test the case of replacing a previous sibling node
        '''
        foo = vlibxml2.newNode('foo')
        bar = vlibxml2.newNode('bar')
        baz = vlibxml2.newNode('baz')
        boo = vlibxml2.newNode('boo')

        foo.addChild(baz)
        foo.addChild(bar)

        baz.replaceNode(boo)
        self.assertEquals(str(baz), '<boo/>')
        self.assertEquals(foo.children(), [boo, bar])

        self.assertEquals(foo.name(), 'foo')
        self.assertEquals(bar.name(), 'bar')
        self.assertEquals(baz.name(), 'boo')
        self.assertEquals(boo.name(), 'boo')


if __name__ == '__main__':
    unittest.main()

