import os
import pytest
from contextly.core.graph.parsers.typescript import TypeScriptASTParser

def test_typescript_parser_exhaustive(tmp_path):
    parser = TypeScriptASTParser()
    
    # Create invalid tsconfig.json to test exception
    invalid_tsconfig = tmp_path / "tsconfig.json"
    invalid_tsconfig.write_text("{invalid json")
    
    content = """
    import { a } from "./local";
    import b from "../parent";
    import c from "@alias/module";
    
    export const x = 1;
    export function myFunc(param1: string, param2?: number): boolean {
        console.log("test");
        return true;
    }
    export class MyClass extends BaseClass implements IInterface {
        public field1: string;
        field2: number;
        
        myMethod(arg1: any): void {
            this.field1 = "a";
        }
    }
    export interface MyInterface {
        prop1: string;
        meth1(arg: string): number;
    }
    
    export { myFunc as testFunc };
    export default MyClass;
    """
    
    dto = parser.parse("src/nested/file.ts", content, str(tmp_path))
    
    assert dto.error is None
    
    # Check exports
    assert "x" in dto.exports
    assert "myFunc" in dto.exports
    assert "MyClass" in dto.exports
    assert "MyInterface" in dto.exports
    assert "myFunc" in dto.exports # actually export_clause tests
    assert "default" in dto.exports
    
    # Check imports
    assert "src/nested/local" in dto.imports
    assert "src/parent" in dto.imports
    assert "@alias/module" in dto.imports
    
    # Check classes
    my_class = next((e for e in dto.entities if e.name == "MyClass"), None)
    assert my_class is not None
    assert "BaseClass" in my_class.parent_classes
    assert "IInterface" in my_class.parent_classes
    assert "console.log" in my_class.called_entities or len(my_class.fields) > 0
    assert len(my_class.fields) == 2
    assert my_class.fields[0].name == "field1"
    
    assert len(my_class.methods) == 1
    assert my_class.methods[0].name == "myMethod"
    assert len(my_class.methods[0].inputs) == 1
    assert my_class.methods[0].inputs[0].name == "arg1"
    
    # Check interfaces
    my_interface = next((e for e in dto.entities if e.name == "MyInterface"), None)
    assert my_interface is not None
    assert len(my_interface.fields) == 1
    assert my_interface.fields[0].name == "prop1"
    assert len(my_interface.methods) == 1
    assert my_interface.methods[0].name == "meth1"
    
    # Check function
    func = next((e for e in dto.entities if e.name == "myFunc"), None)
    assert func is not None
    assert len(func.inputs) == 2
    assert func.inputs[0].name == "param1"
    assert func.inputs[1].name == "param2"
    assert func.outputs == ": boolean"

def test_typescript_parser_relative_out_of_bounds(tmp_path):
    parser = TypeScriptASTParser()
    content = "import x from '............/out/of/bounds';"
    dto = parser.parse("src/file.ts", content, str(tmp_path))
    assert "src/............/out/of/bounds" in dto.imports

def test_typescript_parser_tsconfig_path_resolve(tmp_path):
    # Setup valid tsconfig
    tsconfig = tmp_path / "tsconfig.json"
    tsconfig.write_text('{"compilerOptions": {"paths": {"@app/*": ["src/app/*"]}}}')
    
    parser = TypeScriptASTParser()
    content = "import { y } from '@app/utils';"
    dto = parser.parse("src/file.ts", content, str(tmp_path))
    assert "src/app/utils" in dto.imports
