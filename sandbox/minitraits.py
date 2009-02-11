import types

class AttributeBase(object):
    
    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        try:
            return inst._attributes[self.name]
        except KeyError:
            raise AttributeError("object has no attribute %r" % self.name)
    
    def __set__(self, inst, value):
        actualValue = self.validate(inst, self.name, value)
        inst._attributes[self.name] = actualValue
    
    def validate(self, inst, name, value):
        raise NotImplementedError("validate must be implemented by a subclass")

class NameFinder(type):
    
    def __new__(cls, name, bases, classdict):
        attributeList = []
        for k,v in classdict.iteritems():
            if isinstance(v, AttributeBase):
                v.name = k
                attributeList.append(k)
        classdict['_attributeList'] = attributeList
        return type.__new__(cls, name, bases, classdict)

class HasAttributes(object):
    __metaclass__ = NameFinder
    
    def __init__(self):
        self._attributes = {}
    
    def getAttributeNames(self):
        return self._attributeList
    
    def getAttributesOfType(self, t, default=None):
        result = {}
        for a in self._attributeList:
            if self.__class__.__dict__[a].__class__ == t:
                try:
                    value = getattr(self, a)
                except AttributeError:
                    value = None
                result[a] = value
        return result

class TypedAttribute(AttributeBase):
    
    def validate(self, inst, name, value):
        if type(value) != self._type:
            raise TypeError("attribute %s must be of type %s" % (name, self._type))
        else:
            return value

# class Option(TypedAttribute):
#     
#     _type = types.IntType
# 
# class Param(TypedAttribute):
#     
#     _type = types.FloatType
# 
# class String(TypedAttribute):
#     
#     _type = types.StringType
        
class TypedSequenceAttribute(AttributeBase):
    
    def validate(self, inst, name, value):
        if type(value) != types.TupleType and type(value) != types.ListType:
            raise TypeError("attribute %s must be a list or tuple" % (name))
        else:
            for item in value:
                if type(item) != self._subtype:
                    raise TypeError("attribute %s must be a list or tuple of items with type %s" % (name, self._subtype))
            return value

# class Instance(AttributeBase):
#     
#     def __init__(self, cls):
#         self.cls = cls
#     
#     def validate(self, inst, name, value):
#         if not isinstance(value, self.cls):
#             raise TypeError("attribute %s must be an instance of class %s" % (name, self.cls))
#         else:
#             return value
        

# class OptVec(TypedSequenceAttribute):
#     
#     _subtype = types.IntType
# 
# class PrmVec(TypedSequenceAttribute):
#     
#     _subtype = types.FloatType
# 
# class StrVec(TypedSequenceAttribute):
#     
#     _subtype = types.StringType
# 
# 
# class Bar(HasAttributes):
#     
#     a = Option()
# 
# class Foo(HasAttributes):
#     
#     a = Option()
#     b = Param()
#     c = String()
#     d = OptVec()
#     e = PrmVec()
#     f = StrVec()
#     h = Instance(Bar)