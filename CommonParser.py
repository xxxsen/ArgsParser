#coding = utf-8

import json;
import os;
import traceback;
import sys;
import re;

EXAMPLE = {
    "--num":{"name":"num", "require":True, "validate":"^\d+:\d+$", "type":"string", "short":"-n"},
    "--str":{"require":True, "validate":".+", "type":"int", "optional":[13, 23, 53], "conflict":["-n"], "precond":["-t", "--ac"], "short":"-s", "default":13},
    "--test":{"type":"json", "short":"-t"},
    "--ac":{"name":"ac", "type":"bool"},
    "--xx":{"validate":"^[a-z]+$", "short":"-x"},
    "xt":{"default":3}
};

#=============array====================
FALSE_ARRAY = ["f", "false", "no", "n"];
TRUE_ARRAY = ["t", "true", "yes", "y"];
TYPE_ARRAY = ["string", "int", "json", "bool"];

#=============spec setting=============
ENABLE_INFO = True;
PREFIX = "--";


class StringException(Exception):
    def __init__(self, value):
        self.value_ = value;
        
    def __str__(self):
        return repr(self.value_);

class UnknowTypeException(StringException):
    def __init__(self, value):
        StringException.__init__(self, value);

class UnknowKeyException(StringException):
    def __init__(self, value):
        StringException.__init__(self, value);       
        
class UnParseException(StringException):
    def __init__(self, value):
        StringException.__init__(self, value);

class KeyNotFoundException(StringException):
    def __init__(self, value):
        StringException.__init__(self, value);
    
class IncompatabaleTypeException(StringException):
    def __init__(self, value):
        StringException.__init__(self, value);
        
class IncompatabaleValueException(StringException):
    def __init__(self, value):
        StringException.__init__(self, value);
    
class UnSatisfiedException(StringException):
    def __init__(self, value):
        StringException.__init__(self, value);
        
class CommonParser:
    def __init__(self):
        self.setting_ = {};
        self.parsed_ = {};
        self.shortMap_ = {};
        
    def loadFromFile(self, f):
        with open(f, "r") as file:
            self.loadFromString(f.read());
        
    def loadFromString(self, s):
        try:
            self.loadFromArray(json.loads(s));
        except Exception as e:
            print("Load setting string cause exception:{0}".format(e));
            traceback.print_exc();
        
    def loadFromArray(self, a):
        self.setting_ = a;
        self.shortMap_ = {};
        if(type(self.setting_) != type({})):
            raise IncompatabaleTypeException("Setting string must be a map...");
        #=======correct invalid=========
        for key, value in self.setting_.items():
            if("short" in value):
                if(value["short"] in self.shortMap_):
                    raise UnSatisfiedException("Short key:{0} mapped different long key:{1}, {2}".format(value["short"], key, self.shortMap_[value["short"]]));
                self.shortMap_[value["short"]] = key;
            
            if(ENABLE_INFO and not key.startswith(PREFIX)):
                print("Key:{0} not startswith prefix:{1}".format(key, PREFIX));
            
            if("name" not in value):
                defaultName = key.strip(PREFIX);
                if(ENABLE_INFO):
                    print("key:name not found in value, use:{0} as default.".format(defaultName))
                value.update({"name":defaultName});
            if("type" not in value):
                value["type"] = "string";
            value["type"] = value["type"].lower();
            if("validate" in value):
                if(not value["validate"].startswith("^")):
                    value["validate"] = "^" + value["validate"];
                if(not value["validate"].endswith("$")):
                    value["validate"] = value["validate"] + "$";
            if("require" in value and type(value["require"]) != type(True)):
                if(type(value["require"]) == type(0)): #integer
                    value["require"] = (value["require"] == 0 and False or True);
                elif(type(value["require"]) == type("")):
                    if(value["require"].lower() in FALSE_ARRAY):
                        value["require"] = False;
                    elif(value["require"].lower in TRUE_ARRAY):
                        value["require"] = True;
                raise UnknowTypeException("Unknow value:{0} in key:require".format(value["require"]));
            if("type" in value and value["type"].lower() not in TYPE_ARRAY):
                raise UnknowTypeException("Unknow value:{0} in key:type".format(value["type"]));
        
        if(ENABLE_INFO):
            print("Short key map:{0}".format(self.shortMap_));
        
        for key, value in self.setting_.items():
            #correct conflict
            if("conflict" in value):
                for index, item in enumerate(value["conflict"]):
                    item = self.toLongKey(item);
                    value["conflict"][index] = item;
                    if(item not in self.setting_):
                        raise UnknowTypeException("Unknow item:{0} in key:{1}'s conflicts.".format(item, key));
                    else:
                        if("conflict" in self.setting_[item]):
                            if(key not in self.setting_[item]["conflict"]):
                                self.setting_[item]["conflict"].append(key);
                        else:
                            self.setting_[item]["conflict"] = [key];
            #correct precond
            if("precond" in value):
                for index, item in enumerate(value["precond"]):
                    value["precond"][index] = self.toLongKey(item);
        if(ENABLE_INFO):
            print("Setting:{0}".format(self.setting_));
        
    def toLongKey(self, key):
        if(key in self.shortMap_):
            return self.shortMap_[key];
        return key;
        
    def match(self, pattern, string):
        if(not re.compile(pattern).match(string)):
            return False;
        return True;
        
    def parse(self, arr = []):
        self.parsed_ = {};
        precondList = {};
        
        if(len(arr) == 0):
            arr = sys.argv[1:];
            
        #===init default===
        for k, v in self.setting_.items():
            if("default" in v):
                if("optional" in v and v["default"] not in v["optional"]):
                    raise IncompatabaleTypeException("Default value not expected, value:{0}, optional:{1}".format(v["default"], v["optional"]));
                
                if("validate" in v and not self.match(v["validate"], str(v["default"]))):
                    raise IncompatabaleTypeException("Default value not validate, value:{0}, validate:{1}".format(v["default"], v["validate"]));
                self.parsed_[v["name"]] = v["default"];
            
        for item in arr:
            key, value = item.split("=", 1);
            key = self.toLongKey(key);  # convert to long first..
            if(key not in self.setting_):
                raise UnknowKeyException("Unknow key:{0}....".format(key));
                
            keySetting =  self.setting_[key];
            
            if("validate" in keySetting):
                if(not self.match(keySetting["validate"], value)):
                    raise IncompatabaleTypeException("Validate failed, key:{0}, value:{1}, validate string:{2}".format(key, value, keySetting["validate"]));
            if(keySetting["name"] in self.parsed_ and "default" not in keySetting and ENABLE_INFO):
                print("Multi key found. key:{0}, may use short key and long key?".format(key));
            
            #type conversion...
            try:
                if(keySetting["type"] == "int"):
                    value = int(value);
                elif(keySetting["type"] == "json"):
                    value = json.loads(value);
                elif(keySetting["type"] == "bool"):
                    value = value.lower();
                    if(value in TRUE_ARRAY):
                        value = True;
                    elif(value in FALSE_ARRAY):
                        value = False;
                    else:
                        raise IncompatabaleTypeException("Unknow bool type:{0}, key:{1}".format(value, key));
            except Exception as e:
                raise IncompatabaleTypeException("Converse to type:{0} failed, key:{1}, value:{2}".format(keySetting["type"], key, value));
                    
            #optional value check...
            if("optional" in keySetting and not value in keySetting["optional"]):
                raise IncompatabaleValueException("Key:{0} need value in array:{1}, but got {2}".format(key, keySetting["optional"], value));
                
            #pre condition check...
            if(keySetting["name"] in precondList):
                precondList.pop(keySetting["name"]);
            if("precond" in keySetting):
                for item in keySetting["precond"]:
                    if(self.setting_[item]["name"] not in self.parsed_):
                        if(self.setting_[item]["name"] not in precondList):
                            precondList[self.setting_[item]["name"]] = [keySetting["name"]];
                        else:
                            precondList[self.setting_[item]["name"]].append(keySetting["name"]);

            #conflict check...                
            if("conflict" in keySetting):
                for item in keySetting["conflict"]:
                    if(self.setting_[item]["name"] in self.parsed_):
                        raise UnSatisfiedException("Conflict catched, key:{0}, conflict key:{1}".format(key, item));
            self.parsed_[keySetting["name"]] = value;
        
        if(len(precondList) != 0):
            data = ""
            for k, v in precondList.items():
                data += "key:{0} required by:{1};".format(k, v);
            raise UnSatisfiedException("Pre condition not satisfied:{0}".format(data));
        
    def get(self, key):
        if(len(self.parsed_) == 0):
            raise UnParseException("You should invoke parse method first...");
        if(key not in self.parsed_):
            raise KeyNotFoundException("No key:{0} found in parsed map..".format(key));
        return self.parsed_[key];
        
    def getInt(self, key, default = 0):
        value = "";
        try:
            value = int(self.get(key));
        except KeyNotFoundException as e:
            value = default;
        return value;
        
    def getString(self, key, default = ""):
        value = default;
        try:
            value = self.get(key);
        except KeyNotFoundException as e:
            pass;
        return value;
     
    def getAll(self):
        return self.parsed_;
        
    def load(self, s, type = "string"):
        type == type.lower();
        if(type == "string" or type == "s"):
            return self.loadFromString(s);
        elif(type == "file" or type == "f"):
            return self.loadFromFile(s);
        elif(type == "a" or type == "array"):
            return self.loadFromArray(s);
        else:
            raise UnknowTypeException("Unknow type:{0}".format(type));
        return None;
        
def main():
    p = CommonParser();
    p.load(EXAMPLE, "a");
    p.parse(["--test=[2,3]", "--ac=true", "-x=abc", "--xx=asfdsaf", "xt=3"]);
    print(p.getAll());
    print(p.getInt("--str"));
    print(p.get("test"));
    print(p.get("str"));
    print(p.get("xt"));
    
if(__name__ == "__main__"):
    main();